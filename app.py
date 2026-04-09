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
    st.error("Connexion au tableur impossible. Vérifiez les guillemets et la publication Web.")
    st.stop()

st.title("⚡ Planning Bornes Calais")

for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    # On récupère bien ce qu'il y a déjà dans la file d'attente
    file_actuelle = str(row['Suivant']).strip()
    
    color = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: color = "#fff3cd"

    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{color}; border:1px solid #ccc; margin-bottom:10px; color:black">
            <h3 style="margin:0">🔌 {row['Borne']}</h3>
            <p style="margin:0"><b>Actuel :</b> {row['Utilisateur'] or 'LIBRE'}</p>
            <p style="margin:0"><b>Session :</b> {row['Début']} ⮕ {row['Fin']}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        # Bouton Panne
        label = "🔧 Réparée" if "panne" in statut else "🚩 Panne"
        if st.button(label, key=f"p_{index}", use_container_width=True):
            payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre" if "panne" in statut else "panne", "utilisateur": "", "debut": "", "fin": "", "suivant": file_actuelle}
            requests.post(SCRIPT_URL, json=payload)
            st.rerun()

    with c2:
        # Bouton Libérer (Prend le premier de la file s'il y en a un)
        if "occupe" in statut:
            if st.button("✅ Terminer", key=f"l_{index}", use_container_width=True):
                suivants = [s.strip() for s in file_actuelle.split("|") if s.strip()]
                if suivants:
                    prochain = suivants.pop(0) # On sort le 1er de la liste
                    # On nettoie le texte pour l'utilisateur actuel (on enlève les crochets de date)
                    user_next = prochain.split(" [")[0] if " [" in prochain else prochain
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": user_next, "debut": "Auto", "fin": "Suivant", "suivant": "|".join(suivants)}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- FORMULAIRE DE RÉSERVATION ---
    with st.expander("📅 Réserver un créneau"):
        with st.form(key=f"f_{index}", clear_on_submit=True):
            nom = st.text_input("Ton Prénom")
            date_sel = st.date_input("Pour quel jour ?", value=now.date())
            h_d = st.text_input("Début (ex: 08:00)")
            h_f = st.text_input("Fin (ex: 10:00)")
            
            if st.form_submit_button("Ajouter à la suite"):
                if nom and h_d and h_f:
                    date_str = date_sel.strftime("%d/%m")
                    nouvelle_resa = f"{nom} [{date_str} {h_d}-{h_f}]"
                    
                    # LOGIQUE : Si c'est LIBRE et pour AUJOURD'HUI -> Occupé direct
                    if "libre" in statut and date_sel == now.date():
                        p = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom, "debut": h_d, "fin": h_f, "suivant": file_actuelle}
                    else:
                        # SINON : On l'ajoute à la file SANS EFFACER l'existant
                        if file_actuelle == "":
                            file_mise_a_jour = nouvelle_resa
                        else:
                            file_mise_a_jour = f"{file_actuelle} | {nouvelle_resa}"
                        
                        p = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": row['Utilisateur'], "debut": row['Début'], "fin": row['Fin'], "suivant": file_mise_a_jour}
                    
                    requests.post(SCRIPT_URL, json=p)
                    st.success("Planning mis à jour !")
                    time.sleep(1)
                    st.rerun()

    # Affichage propre de la file
    if file_actuelle:
        st.write("📋 **Réservations à venir :**")
        for i, res in enumerate(file_actuelle.split("|")):
            if res.strip():
                st.caption(f"{i+1}. {res.strip()}")
    st.divider()
