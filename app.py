import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzM3-IddG1w-dcRWWFn26GZeLyixxQ8bu0QZ_EIqEluMf2h33VPDTXsWv5Cc-LvGMWk/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais Pro", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LECTURE ---
try:
    # On force la lecture la plus fraîche possible
    df = pd.read_csv(f"{SHEET_CSV}&refresh={now.timestamp()}").fillna("")
    df.columns = df.columns.str.strip()
except:
    st.error("Connexion au Sheets impossible.")
    st.stop()

st.title("⚡ Réseau Bornes Calais")
st.write(f"🕒 Heure : **{now.strftime('%H:%M')}**")

for index, row in df.iterrows():
    # On stocke les données de la ligne dans des variables propres
    b_name = str(row['Borne'])
    b_lieu = str(row['Lieu'])
    b_statut = str(row['Statut']).lower()
    b_user = str(row['Utilisateur'])
    b_deb = str(row['Début'])
    b_fin = str(row['Fin'])
    # On nettoie la file d'attente pour éviter les textes bizarres
    b_suivant = str(row['Suivant']).strip()
    if b_suivant.lower() == "nan": b_suivant = ""

    # Couleur
    color = "#d4edda" if "libre" in b_statut else "#f8d7da"
    if "panne" in b_statut: color = "#fff3cd"

    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{color}; border:1px solid #ccc; margin-bottom:10px; color:black">
            <h3 style="margin:0">🔌 {b_name} ({b_lieu})</h3>
            <p style="margin:0"><b>Actuel :</b> {b_user if b_user else 'Disponible'}</p>
            <p style="margin:0"><b>Horaire :</b> {b_deb} ⮕ {b_fin}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        # État Panne / Réparée
        label = "🔧 Réparée" if "panne" in b_statut else "🚩 Panne"
        if st.button(label, key=f"p_{index}", use_container_width=True):
            new_s = "libre" if "panne" in b_statut else "panne"
            p = {"row": index+1, "borne": b_name, "lieu": b_lieu, "statut": new_s, "utilisateur": "", "debut": "", "fin": "", "suivant": b_suivant}
            requests.post(SCRIPT_URL, json=p)
            st.rerun()

    with c2:
        # Libérer (Prendre le suivant)
        if "occupe" in b_statut:
            if st.button("✅ Terminer", key=f"l_{index}", use_container_width=True):
                items = [i.strip() for i in b_suivant.split("|") if i.strip()]
                if items:
                    prochain = items.pop(0)
                    # Extraction sécurisée du nom et des heures
                    try:
                        p_nom = prochain.split(" [")[0]
                        p_h = prochain.split("[")[1].split("]")[0].split(" ")[1].split("-")
                        p_d, p_f = p_h[0], p_h[1]
                    except:
                        p_nom = prochain; p_d = "Auto"; p_f = "En cours"
                    
                    p = {"row": index+1, "borne": b_name, "lieu": b_lieu, "statut": "occupé", "utilisateur": p_nom, "debut": p_d, "fin": p_f, "suivant": "|".join(items)}
                else:
                    p = {"row": index+1, "borne": b_name, "lieu": b_lieu, "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=p)
                st.rerun()

    # --- FORMULAIRE RÉSERVATION SÉCURISÉ ---
    with st.expander("📅 Réserver / Prendre la place"):
        with st.form(key=f"form_{index}", clear_on_submit=True):
            f_nom = st.text_input("Ton Prénom")
            f_date = st.date_input("Date", value=now.date())
            f_h_d = st.text_input("Heure Début (ex: 08:00)")
            f_h_f = st.text_input("Heure Fin (ex: 10:00)")
            
            if st.form_submit_button("Valider la réservation"):
                if f_nom and f_h_d and f_h_f:
                    # On crée le texte de la nouvelle réservation
                    d_str = f_date.strftime("%d/%m")
                    nouvelle_resa = f"{f_nom} [{d_str} {f_h_d}-{f_h_f}]"

                    # LOGIQUE ANTI-EFFACEMENT
                    if "libre" in b_statut and f_date == now.date():
                        # LIBRE : On prend la place
                        payload = {"row": index+1, "borne": b_name, "lieu": b_lieu, "statut": "occupé", "utilisateur": f_nom, "debut": f_h_d, "fin": f_h_f, "suivant": b_suivant}
                    else:
                        # OCCUPÉ ou FUTUR : On AJOUTE à la liste sans écraser
                        if b_suivant == "":
                            file_finale = nouvelle_resa
                        else:
                            # On vérifie si la personne n'est pas déjà dans la file
                            file_finale = f"{b_suivant} | {nouvelle_resa}"
                        
                        payload = {"row": index+1, "borne": b_name, "lieu": b_lieu, "statut": b_statut, "utilisateur": b_user, "debut": b_deb, "fin": b_fin, "suivant": file_finale}
                    
                    requests.post(SCRIPT_URL, json=payload)
                    st.success("Réservation enregistrée !")
                    time.sleep(1.5) # Pause pour laisser Google Sheets respirer
                    st.rerun()

    # Affichage de la file
    if b_suivant:
        st.write("📋 **Planning à venir :**")
        for i, r in enumerate(b_suivant.split("|")):
            st.caption(f"{i+1}. {r.strip()}")
    st.divider()
