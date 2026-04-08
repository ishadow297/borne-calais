import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Planning Bornes Calais", page_icon="⚡")
st.title("⚡ Planning des Bornes")

# Connexion au fichier
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Nettoyage des colonnes au cas où
for c in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if c not in df.columns:
        df[c] = ""

# --- PARTIE 1 : ÉTAT ACTUEL ---
st.header("📍 État des bornes (Maintenant)")
for index, row in df.iterrows():
    with st.expander(f"{row['Borne']} - {'🟢 LIBRE' if str(row['Statut']).lower() == 'libre' else '🔴 OCCUPÉ'}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Actuel :** {row['Utilisateur']}")
            st.write(f"**Fin prévue :** {row['Heure de fin']}")
            if pd.notna(row['Suivant']) and row['Suivant'] != "":
                st.info(f"⏳ Prochain : {row['Suivant']}")

        with col2:
            if st.button(f"Libérer {row['Borne']}", key=f"lib_{index}"):
                df.at[index, 'Statut'] = "libre"
                df.at[index, 'Utilisateur'] = ""
                df.at[index, 'Heure de fin'] = ""
                df.at[index, 'Suivant'] = ""
                conn.update(data=df)
                st.rerun()

# --- PARTIE 2 : RÉSERVATION / MISE À JOUR ---
st.divider()
st.header("📝 Réserver ou mettre à jour")

with st.form("form_reservation"):
    borne_choisie = st.selectbox("Choisir la borne", df['Borne'].unique())
    type_action = st.radio("Action", ["Je me branche maintenant", "Je réserve pour plus tard / demain"])
    nom = st.text_input("Ton prénom")
    details = st.text_input("Heure de fin (ou jour/heure pour plus tard)", placeholder="ex: Aujourd'hui 18h ou Demain 10h")
    
    submit = st.form_submit_button("Enregistrer")
    
    if submit:
        if nom and details:
            idx = df[df['Borne'] == borne_choisie].index[0]
            if type_action == "Je me branche maintenant":
                df.at[idx, 'Statut'] = "Occupé"
                df.at[idx, 'Utilisateur'] = nom
                df.at[idx, 'Heure de fin'] = details
            else:
                df.at[idx, 'Suivant'] = f"{nom} ({details})"
            
            conn.update(data=df)
            st.success("C'est enregistré ! Le planning est à jour.")
            st.rerun()
        else:
            st.error("Merci de remplir ton nom et l'heure.")
