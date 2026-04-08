import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfr__TekrEpJGmVEu1SvGqRVIppFOQDQJ_MUp7_lwxSRDZ5NAFVlnoThtybQ7IuZlM/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/export?format=csv"

st.set_page_config(page_title="Bornes Automatiques", page_icon="⚡")
st.title("⚡ Planning Borne calais")

# Gestion de l'heure actuelle (France)
now = datetime.now() + timedelta(hours=0) # Ajuste si le serveur n'est pas à l'heure
heure_actuelle = now.strftime("%H:%M")

# Lecture des données
df = pd.read_csv(SHEET_CSV).fillna("")

# --- FONCTION DE NETTOYAGE AUTO ---
def check_status(row):
    if str(row['Statut']).lower() == "occupé":
        # Si l'heure actuelle est plus grande que l'heure de fin, on libère visuellement
        if heure_actuelle > str(row['Heure de fin']):
            return "libre"
    return row['Statut']

# --- AFFICHAGE ---
st.header(f"🕒 Il est {heure_actuelle}")

for index, row in df.iterrows():
    statut_reel = check_status(row)
    is_libre = statut_reel.lower() == "libre"
    
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            icon = "🟢" if is_libre else "🔴"
            st.subheader(f"{icon} {row['Borne']}")
            if not is_libre:
                st.write(f"👤 **{row['Utilisateur']}** jusqu'à **{row['Heure de fin']}**")
            else:
                st.write("✅ Disponible")
        
        with col2:
            if not is_libre:
                if st.button("Libérer maintenant", key=f"btn_{index}"):
                    payload = {"row": index + 1, "borne": row['Borne'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": row['Suivant']}
                    requests.post(SCRIPT_URL, json=payload)
                    st.rerun()

# --- RÉSERVATION ---
st.divider()
st.subheader("📅 Se brancher")

# Liste d'heures toutes les 30min
heures_possibles = [(datetime.now() + timedelta(minutes=x)).strftime("%H:%M") for x in range(30, 480, 30)]

with st.form("resa"):
    b_nom = st.selectbox("Borne", df['Borne'].unique())
    nom = st.text_input("Ton prénom")
    h_fin = st.selectbox("Heure de fin prévue", heures_possibles)
    
    if st.form_submit_button("VALIDER"):
        if nom:
            idx = df[df['Borne'] == b_nom].index[0]
            payload = {
                "row": idx + 1,
                "borne": b_nom,
                "statut": "Occupé",
                "utilisateur": nom,
                "heure": h_fin,
                "suivant": "" # On peut vider la file ici pour simplifier
            }
            requests.post(SCRIPT_URL, json=payload)
            st.success(f"C'est noté {nom} ! Borne réservée jusqu'à {h_fin}")
            st.rerun()
