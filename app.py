import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais Pro", page_icon="⚡", layout="centered")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .status-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd; }
    .libre { background-color: #d4edda; border-left: 10px solid #28a745; }
    .occupe { background-color: #f8d7da; border-left: 10px solid #dc3545; }
    .panne { background-color: #fff3cd; border-left: 10px solid #ffc107; }
    .lieu-text { color: #666; font-size: 0.9em; font-style: italic; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- TEMPS ---
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)
date_j = now.strftime("%d/%m")
heure_j = now.strftime("%H:%M")

# Lecture robuste
try:
    df = pd.read_csv(f"{SHEET_CSV}&cache={now.second}")
    df.columns = df.columns.str.strip()
    df = df.fillna("")
except:
    st.error("Impossible de lire le tableau. Vérifie le partage 'Public'.")
    st.stop()

st.title("⚡ Bornes de Recharge")
st.info(f"🕒 Il est **{heure_j}** | Chaque prise est indépendante.")

# --- AFFICHAGE DES BORNES ---
for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    
    # Choix de la couleur
    css_class = "libre"
    icon = "✅"
    if "occupe" in statut:
        css_class = "occupe"
        icon = "🚗"
    elif "panne" in statut:
        css_class = "panne"
        icon = "⚠️"

    # Affichage de la carte
    st.markdown(f"""
        <div class="status-card {css_class}">
            <h4 style='margin:0;'>{icon} {row['Borne']}</h4>
            <p class="lieu-text">📍 {row['Lieu']}</p>
            <p style='margin:0;'><b>État :</b> {statut.upper()}</p>
        </div>
    """, unsafe_allow_html=True)

    # Boutons d'action
    c1, c2 = st.columns(2)
    
    with c1:
        if "panne" in statut:
            # BOUTON RÉPARER : Apparaît seulement si en panne
            if st.button(f"🔧 Borne Réparée", key=f"fix_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()
        else:
            if st.button(f"🚩 Signaler Panne", key=f"p_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "panne", "utilisateur": "S.O.S", "heure": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    with c2:
        if "occupe" in statut:
            if st.button(f"🔄 Libérer Prise", key=f"l_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    if row['Suivant']:
        with st.expander("📅 Voir la file d'attente"):
            st.write(row['Suivant'].replace(" | ", "\n\n"))

# --- RÉSERVATION (Suite du code identique...) ---
