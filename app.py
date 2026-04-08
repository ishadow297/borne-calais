import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡", layout="wide")

st.title("⚡ Planning des Bornes Calais")

# Connexion (Utilise les Secrets que tu as remplis sur Streamlit)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
except Exception as e:
    st.error("Connexion impossible. Vérifie tes 'Secrets' sur Streamlit.")
    st.stop()

# Nettoyage des colonnes pour éviter les crashs de type
for c in ['Borne', 'Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if c not in df.columns:
        df[c] = ""
    df[c] = df[c].astype(str).replace('nan', '')

# --- PARTIE 1 : ÉTAT ACTUEL ---
st.header("📍 État des bornes maintenant")
cols = st.columns(len(df))

for i, row in df.iterrows():
    with cols[i]:
        status = row['Statut'].lower().strip()
        color = "green" if status == "libre" else "red"
        st.markdown(f"### {row['Borne']}")
        st.markdown(f":{color}[**{status.upper()}**]")
        
        if status != "libre":
            st.write(f"👤 {row['Utilisateur']}")
            st.write(f"⏰ Fin : {row['Heure de fin']}")
        
        if row['Suivant']:
            st.info(f"📅 Résas : {row['Suivant']}")

# --- PARTIE 2 : RÉSERVER ---
st.divider()
st.header("📝 Réserver mon créneau")

with st.form("resa_form"):
    b_select = st.selectbox("Quelle borne ?", df['Borne'].tolist())
    moment = st.radio("Quand ?", ["Maintenant (Je me branche)", "Plus tard (Demain / +2j)"])
    nom = st.text_input("Ton prénom")
    h_fin = st.text_input("Jour et Heure", placeholder="ex: Demain 10h / Ce soir 19h")
    
    if st.form_submit_button("VALIDER MA RÉSERVATION"):
        if nom and h_fin:
            idx = df[df['Borne'] == b_select].index[0]
            if moment == "Maintenant (Je me branche)":
                df.at[idx, 'Statut'] = "Occupé"
                df.at[idx, 'Utilisateur'] = nom
                df.at[idx, 'Heure de fin'] = h_fin
            else:
                # On ajoute à la liste des réservations futures
                old_res = df.at[idx, 'Suivant']
                df.at[idx, 'Suivant'] = f"{old_res} | {nom}({h_fin})".strip(" | ")
            
            conn.update(data=df)
            st.success("C'est enregistré dans le planning !")
            st.rerun()
        else:
            st.warning("Remplis ton nom et l'heure !")

if st.button("🔄 Rafraîchir le planning"):
    st.rerun()
