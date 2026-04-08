import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Planning Bornes Calais", page_icon="⚡")
st.title("⚡ Planning de Recharge")

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Nettoyage automatique des données pour éviter les erreurs de type
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].astype(str).replace('nan', '')

# --- AFFICHAGE ---
st.header("📍 État actuel")
for index, row in df.iterrows():
    status = str(row['Statut']).strip().lower()
    with st.expander(f"{row['Borne']} - {'🟢 LIBRE' if status == 'libre' else '🔴 OCCUPÉ'}"):
        st.write(f"👤 **Utilisateur :** {row['Utilisateur']}")
        st.write(f"⏰ **Fin :** {row['Heure de fin']}")
        if row['Suivant']:
            st.warning(f"⏳ Futur : {row['Suivant']}")
            
        if st.button(f"Libérer {row['Borne']}", key=f"lib_{index}"):
            df.at[index, 'Statut'] = "libre"
            df.at[index, 'Utilisateur'] = ""
            df.at[index, 'Heure de fin'] = ""
            conn.update(data=df)
            st.rerun()

# --- RÉSERVATION ---
st.divider()
st.header("📅 Réserver (Auj, Demain, +2j)")
with st.form("planning"):
    b = st.selectbox("Borne", df['Borne'].unique())
    act = st.radio("Moment", ["Maintenant", "Plus tard"])
    nom = st.text_input("Prénom")
    h = st.text_input("Jour / Heure (ex: Demain 14h)")
    
    if st.form_submit_button("Enregistrer"):
        if nom and h:
            idx = df[df['Borne'] == b].index[0]
            if act == "Maintenant":
                df.at[idx, 'Statut'] = "Occupé"
                df.at[idx, 'Utilisateur'] = nom
                df.at[idx, 'Heure de fin'] = h
            else:
                old = str(df.at[idx, 'Suivant'])
                df.at[idx, 'Suivant'] = f"{old} | {nom}({h})".strip(" | ")
            
            conn.update(data=df)
            st.success("C'est enregistré !")
            st.rerun()
