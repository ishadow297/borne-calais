import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais Pro", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LECTURE SANS CACHE ---
try:
    df = pd.read_csv(f"{SHEET_CSV}&refresh={now.timestamp()}").fillna("")
    df.columns = df.columns.str.strip()
except:
    st.error("Connexion au tableur impossible.")
    st.stop()

st.title("⚡ Planning Multi-Dates Bornes")
st.write(f"🕒 Heure actuelle : **{now.strftime('%H:%M')}**")

for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    file_attente = str(row['Suivant'])
    
    # Couleur de la borne
    color = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: color = "#fff3cd"

    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{color}; border:1px solid #ccc; margin-bottom:10px; color:black">
            <h3 style="margin:0">🔌 {row['Borne']}</h3>
            <p style="margin:0"><b>Utilisateur actuel :</b> {row['Utilisateur'] or 'LIBRE'}</p>
            <p style="margin:0"><b>Session :</b> {row['Début']} ⮕ {row['Fin']}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        # Bouton Panne
        label = "🔧 Réparée" if "panne" in statut else "🚩 Panne"
        if st.button(label, key=f"p_{index}", use_container_width=True):
            payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre" if "panne" in statut else "panne", "utilisateur": "", "debut": "", "fin": "", "suivant": file_attente}
            requests.post(SCRIPT_URL, json=payload)
            with st.spinner("Mise à jour..."): time.sleep(2)
            st.rerun()

    with c2:
        # Bouton Libérer
        if "occupe" in statut:
            if st.button("✅ Terminer", key=f"l_{index}", use_container_width=True):
                suivants = [s.strip() for s in file_attente.split("|") if s.strip()]
                if suivants:
                    p = suivants.pop(0) # On sort le prochain de la file
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": p, "debut": "Auto", "fin": "Suivant", "suivant": "|".join(suivants)}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                with st.spinner("Chargement..."): time.sleep(2)
                st.rerun()

    # --- FORMULAIRE DE RÉSERVATION AVEC CALENDRIER ---
    with st.expander("📅 Réserver un créneau (Choisir la date)"):
        with st.form(key=f"form_{index}", clear_on_submit=True):
            nom = st.text_input("Prénom")
            date_choisie = st.date_input("Date de réservation", value=now.date())
            colh1, colh2 = st.columns(2)
            h_d = colh1.text_input("Heure Début (ex: 08:00)")
            h_f = colh2.text_input("Heure Fin (ex: 10:30)")
            
            if st.form_submit_button("Ajouter au planning"):
                if nom and h_d and h_f:
                    date_str = date_choisie.strftime("%d/%m")
                    info_complet = f"{nom} [{date_str} {h_d}-{h_f}]"
                    
                    # Si la borne est libre ET que c'est pour AUJOURD'HUI
                    if "libre" in statut and date_choisie == now.date():
                        p = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom, "debut": h_d, "fin": h_f, "suivant": file_attente}
                    else:
                        # Sinon, on ajoute TOUJOURS à la suite dans la file
                        nouvelle_file = f"{file_attente} | {info_complet}" if file_attente else info_complet
                        p = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": row['Utilisateur'], "debut": row['Début'], "fin": row['Fin'], "suivant": nouvelle_file}
                    
                    requests.post(SCRIPT_URL, json=p)
                    st.success(f"Réservé pour le {date_str} !")
                    time.sleep(2)
                    st.rerun()

    if file_attente:
        st.write("📋 **Planning des réservations :**")
        for i, res in enumerate(file_attente.split("|")):
            if res.strip():
                st.caption(f"{i+1}. {res.strip()}")
    st.divider()
