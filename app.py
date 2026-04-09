import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LECTURE SANS CACHE (OPTIMISÉE) ---
try:
    # On utilise un timestamp unique pour forcer Google à rafraîchir
    df = pd.read_csv(f"{SHEET_CSV}&refresh={now.timestamp()}").fillna("")
    df.columns = df.columns.str.strip()
except:
    st.error("Connexion perdue avec le tableur.")
    st.stop()

st.title("⚡ Planning Bornes Calais")
st.write(f"🕒 Heure du site : **{now.strftime('%H:%M')}**")

for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    file_attente = str(row['Suivant'])
    
    # Design de la carte
    color = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: color = "#fff3cd"

    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{color}; border:1px solid #ccc; margin-bottom:10px; color:black">
            <h3 style="margin:0">🔌 {row['Borne']}</h3>
            <p style="margin:0"><b>Utilisateur :</b> {row['Utilisateur'] or 'LIBRE'}</p>
            <p style="margin:0"><b>Début :</b> {row['Début'] or '--:--'} | <b>Fin prévue :</b> {row['Fin'] or '--:--'}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        # Bouton Panne / Réparée
        label = "🔧 Réparée" if "panne" in statut else "🚩 Panne"
        new_statut = "libre" if "panne" in statut else "panne"
        if st.button(label, key=f"btn_p_{index}", use_container_width=True):
            payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": new_statut, "utilisateur": "", "debut": "", "fin": "", "suivant": file_attente}
            requests.post(SCRIPT_URL, json=payload)
            with st.spinner("Mise à jour Google..."): time.sleep(2)
            st.rerun()

    with c2:
        # Bouton Libérer / Suivant
        if "occupe" in statut:
            if st.button("✅ Terminer", key=f"btn_l_{index}", use_container_width=True):
                suivants = [s.strip() for s in file_attente.split("|") if s.strip()]
                if suivants:
                    p = suivants.pop(0)
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": p, "debut": "Auto", "fin": "Suivant", "suivant": "|".join(suivants)}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                with st.spinner("Chargement..."): time.sleep(2)
                st.rerun()

    # --- FORMULAIRE DE RÉSERVATION ---
    with st.expander("📅 Réserver (Ajouter au planning)"):
        with st.form(key=f"f_{index}", clear_on_submit=True):
            nom = st.text_input("Prénom")
            h_debut = st.text_input("Début (ex: 11:30)")
            h_fin = st.text_input("Fin (ex: 13:00)")
            if st.form_submit_button("Valider la réservation"):
                if nom and h_debut and h_fin:
                    info = f"{nom} ({h_debut}-{h_fin})"
                    if "libre" in statut:
                        p = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom, "debut": h_debut, "fin": h_fin, "suivant": file_attente}
                    else:
                        nouvelle_file = f"{file_attente} | {info}" if file_attente else info
                        p = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": row['Utilisateur'], "debut": row['Début'], "fin": row['Fin'], "suivant": nouvelle_file}
                    
                    requests.post(SCRIPT_URL, json=p)
                    st.success("Enregistré !")
                    time.sleep(2)
                    st.rerun()

    if file_attente:
        st.caption(f"📋 File d'attente : {file_attente}")
    st.divider()
