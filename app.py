import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw9JYdBbRQ2HlQo4XbXXDooR5cc2yVEvQK4IhV3a4xkkT62XgJCP98lgs8OWkBF-ROq/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# Lecture fraîche
df = pd.read_csv(f"{SHEET_CSV}&v={time.time()}").fillna("")
df.columns = df.columns.str.strip()

st.title("⚡ Bornes de Recharge Calais")

for index, row in df.iterrows():
    borne = str(row['Borne'])
    statut = str(row['Statut']).lower()
    file_attente = str(row['Suivant'])

    # Affichage de la borne
    color = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: color = "#fff3cd"
    
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{color}; border:1px solid #ccc; color:black; margin-bottom:10px">
            <h3>🔌 {borne}</h3>
            <p><b>Utilisateur :</b> {row['Utilisateur'] or 'Libre'}</p>
            <p><b>Fin :</b> {row['Fin'] or '---'}</p>
        </div>
    """, unsafe_allow_html=True)

    # ACTIONS
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚩 Panne", key=f"p_{index}"):
            p = {"action": "MAJ", "row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HS", "debut": "", "fin": "", "suivant": file_attente}
            requests.post(SCRIPT_URL, json=p)
            st.rerun()
    with c2:
        if "occupé" in statut:
            if st.button("✅ Terminer", key=f"l_{index}"):
                # Logique simplifiée pour libérer
                p = {"action": "MAJ", "row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=p)
                st.rerun()

    # FORMULAIRE DE RESERVATION
    with st.expander("📅 Réserver"):
        with st.form(key=f"f_{index}", clear_on_submit=True):
            f_nom = st.text_input("Prénom")
            f_date = st.date_input("Date", value=now.date())
            f_h = st.selectbox("Heure", [f"{h:02d}:00" for h in range(24)])
            
            if st.form_submit_button("Confirmer"):
                if f_nom:
                    resa_txt = f"{f_nom} [{f_date.strftime('%d/%m')} {f_h}]"
                    
                    if statut == "libre" and f_date == now.date():
                        # Cas 1 : Borne libre, on prend la place tout de suite
                        payload = {
                            "action": "MAJ", "row": index+1, "borne": borne, "lieu": row['Lieu'],
                            "statut": "occupé", "utilisateur": f_nom, "debut": "Maintenant", "fin": f_h, "suivant": file_attente
                        }
                    else:
                        # Cas 2 : On demande au SCRIPT GOOGLE de rajouter à la file
                        # C'est ici que la magie opère pour ne rien effacer
                        payload = {
                            "action": "RESERVER", 
                            "row": index+1, 
                            "reservation": resa_txt
                        }
                    
                    requests.post(SCRIPT_URL, json=payload)
                    st.success("Enregistré !")
                    time.sleep(2)
                    st.rerun()

    if file_attente and file_attente != "nan":
        st.caption(f"File d'attente : {file_attente}")
    st.divider()
