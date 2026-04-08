import streamlit as st
import pandas as pd
import requests

# REMPLACE CETTE URL PAR CELLE COPIÉE À L'ÉTAPE PRÉCÉDENTE
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfr__TekrEpJGmVEu1SvGqRVIppFOQDQJ_MUp7_lwxSRDZ5NAFVlnoThtybQ7IuZlM/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/export?format=csv"

st.title("⚡ Planning Bornes Calais")

# Lecture simple (toujours gratuit)
df = pd.read_csv(SHEET_CSV).fillna("")

for index, row in df.iterrows():
    with st.expander(f"📍 {row['Borne']} - {row['Statut']}"):
        st.write(f"👤 {row['Utilisateur']} | ⏰ Fin : {row['Heure de fin']}")
        
        # Formulaire de mise à jour
        nom = st.text_input("Ton prénom", key=f"n_{index}")
        quand = st.text_input("Heure/Jour", key=f"q_{index}")
        
        if st.button("Enregistrer", key=f"b_{index}"):
            payload = {
                "row": index + 1,
                "borne": row['Borne'],
                "statut": "Occupé",
                "utilisateur": nom,
                "heure": quand,
                "suivant": row['Suivant']
            }
            requests.post(SCRIPT_URL, json=payload)
            st.success("C'est envoyé ! Rafraîchis la page dans 5 secondes.")
