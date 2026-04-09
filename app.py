import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxavX9psS3Spm75cMZJ2F3W7uxiFU1y4E4IdvUcRCPLNAiWDBaoS2I2vLNXYVwgh4oz/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais Pro", page_icon="⚡", layout="wide")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LECTURE DES DONNÉES ---
try:
    # Anti-cache pour avoir les infos en temps réel
    df = pd.read_csv(f"{SHEET_CSV}&v={now.timestamp()}").fillna("")
    df.columns = df.columns.str.strip()
except:
    st.error("Impossible de lire le Sheets. Vérifie la publication Web.")
    st.stop()

st.title("⚡ Réseau de Bornes - Calais")
st.write(f"🕒 Heure actuelle : **{now.strftime('%H:%M')}**")

# --- AFFICHAGE DES BORNES ---
for index, row in df.iterrows():
    # Extraction des infos de la ligne
    borne = str(row['Borne'])
    lieu = str(row['Lieu'])
    statut = str(row['Statut']).lower()
    user = str(row['Utilisateur'])
    debut = str(row['Début'])
    fin = str(row['Fin'])
    suivant = str(row['Suivant']).strip()

    # Style selon l'état
    bg = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: bg = "#fff3cd"

    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{bg}; border:1px solid #ccc; margin-bottom:10px; color:black">
            <h3 style="margin:0">🔌 {borne} — <small>{lieu}</small></h3>
            <p style="margin:0"><b>Utilisateur :</b> {user if user else 'DISPONIBLE'}</p>
            <p style="margin:0"><b>Horaire :</b> {debut} ⮕ {fin if fin else 'Libre'}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        # Signaler Panne / Réparée
        btn_label = "🔧 Réparée" if "panne" in statut else "🚩 Signaler Panne"
        if st.button(btn_label, key=f"p_{index}"):
            new_s = "libre" if "panne" in statut else "panne"
            payload = {"row": index+1, "borne": borne, "lieu": lieu, "statut": new_s, "utilisateur": "", "debut": "", "fin": "", "suivant": suivant}
            requests.post(SCRIPT_URL, json=payload)
            st.rerun()

    with c2:
        # Libérer la borne (Prendre le suivant s'il existe)
        if "occupe" in statut:
            if st.button("✅ Terminer Charge", key=f"l_{index}"):
                items = [i.strip() for i in suivant.split("|") if i.strip()]
                if items:
                    next_res = items.pop(0)
                    # Extraction simple du nom et des heures
                    next_user = next_res.split(" [")[0]
                    next_times = next_res.split("[")[1].split("]")[0].split(" ")[1].split("-")
                    payload = {"row": index+1, "borne": borne, "lieu": lieu, "statut": "occupé", "utilisateur": next_user, "debut": next_times[0], "fin": next_times[1], "suivant": "|".join(items)}
                else:
                    payload = {"row": index+1, "borne": borne, "lieu": lieu, "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- FORMULAIRE RÉSERVATION ---
    with st.expander("📅 Réserver ou Prendre cette borne"):
        with st.form(key=f"f_{index}", clear_on_submit=True):
            f_nom = st.text_input("Nom / Prénom")
            f_date = st.date_input("Date", value=now.date())
            col1, col2 = st.columns(2)
            f_h_deb = col1.text_input("Heure Début (ex: 14:00)")
            f_h_fin = col2.text_input("Heure Fin (ex: 16:30)")
            
            if st.form_submit_button("Confirmer"):
                if f_nom and f_h_deb and f_h_fin:
                    date_str = f_date.strftime("%d/%m")
                    nouvelle_resa = f"{f_nom} [{date_str} {f_h_deb}-{f_h_fin}]"

                    # SI LIBRE et AUJOURD'HUI -> On prend la place
                    if "libre" in statut and f_date == now.date():
                        payload = {"row": index+1, "borne": borne, "lieu": lieu, "statut": "occupé", "utilisateur": f_nom, "debut": f_h_deb, "fin": f_h_fin, "suivant": suivant}
                    # SI DÉJÀ PRIS ou FUTUR -> On ajoute à la file "Suivant"
                    else:
                        file_maj = f"{suivant} | {nouvelle_resa}" if (suivant and suivant != "nan") else nouvelle_resa
                        payload = {"row": index+1, "borne": borne, "lieu": lieu, "statut": statut, "utilisateur": user, "debut": debut, "fin": fin, "suivant": file_maj}
                    
                    requests.post(SCRIPT_URL, json=payload)
                    st.success("Planning mis à jour !")
                    time.sleep(1.5)
                    st.rerun()

    # Affichage de la file d'attente
    if suivant and suivant != "nan":
        st.caption(f"📋 **File d'attente :** {suivant}")
    st.divider()
