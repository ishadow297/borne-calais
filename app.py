import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("⚡ Planning Bornes Calais")

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Nettoyage de sécurité pour éviter les erreurs de tes photos
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns: df[col] = ""
    df[col] = df[col].astype(str).replace('nan', '')

# Affichage simple
for index, row in df.iterrows():
    with st.expander(f"📍 {row['Borne']} - {row['Statut']}"):
        st.write(f"👤 Actuel : {row['Utilisateur']} | ⏰ Fin : {row['Heure de fin']}")
        if row['Suivant']: st.info(f"📅 Réservations : {row['Suivant']}")
        
        if st.button(f"Libérer {row['Borne']}", key=f"lib_{index}"):
            df.at[index, 'Statut'], df.at[index, 'Utilisateur'], df.at[index, 'Heure de fin'] = "libre", "", ""
            conn.update(data=df)
            st.rerun()

# Formulaire de réservation
st.divider()
with st.form("resa"):
    b = st.selectbox("Borne", df['Borne'].unique())
    nom = st.text_input("Ton prénom")
    quand = st.text_input("Jour / Heure (ex: Demain 14h)")
    if st.form_submit_button("Enregistrer"):
        idx = df[df['Borne'] == b].index[0]
        df.at[idx, 'Statut'], df.at[idx, 'Utilisateur'], df.at[idx, 'Heure de fin'] = "Occupé", nom, quand
        conn.update(data=df)
        st.success("Réservé !")
        st.rerun()
