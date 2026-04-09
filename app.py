import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LECTURE ---
try:
    df = pd.read_csv(f"{SHEET_CSV}&nocache={now.microsecond}").fillna("")
    df.columns = df.columns.str.strip()
except:
    st.error("Erreur de lecture du tableau.")
    st.stop()

# --- ENTÊTE AVEC HEURE ACTUELLE ---
st.title("⚡ Planning des Bornes")
st.metric("Heure locale", now.strftime("%H:%M"))

for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    
    # Couleurs
    bg_color = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: bg_color = "#fff3cd"

    # --- CARTE DE LA BORNE ---
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{bg_color}; border:1px solid #ccc; margin-bottom:10px">
            <h3 style="margin:0">🔌 {row['Borne']}</h3>
            <p style="margin:0">📍 {row['Lieu']}</p>
            <hr style="margin:10px 0">
            <p style="margin:0"><b>Utilisateur :</b> {row['Utilisateur'] if row['Utilisateur'] else 'LIBRE'}</p>
            <p style="margin:0">⌚ <b>Créneau :</b> {row['Début']} { 'à' if row['Fin'] else ''} {row['Fin']}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        if "panne" in statut:
            if st.button(f"🔧 Réparée", key=f"fix_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload); st.rerun()
        else:
            if st.button(f"🚩 Panne", key=f"p_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HS", "debut": "", "fin": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload); st.rerun()

    with c2:
        if "occupe" in statut:
            if st.button(f"✅ Libérer / Suivant", key=f"lib_{index}"):
                suivants = str(row['Suivant']).split(" | ") if row['Suivant'] else []
                suivants = [s for s in suivants if s.strip()]
                
                if suivants:
                    p_brut = suivants.pop(0) # ex: "Julien (11:00-13:00)"
                    try:
                        p_nom = p_brut.split(" (")[0]
                        p_heures = p_brut.split(" (")[1].replace(")", "").split("-")
                        p_deb, p_fin = p_heures[0], p_heures[1]
                    except:
                        p_nom = p_brut; p_deb = "En cours"; p_fin = ""
                        
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": p_nom, "debut": p_deb, "fin": p_fin, "suivant": " | ".join(suivants)}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload); st.rerun()

    # --- FORMULAIRE RÉSERVATION ---
    with st.expander("📅 Réserver un créneau"):
        nom_res = st.text_input("Prénom", key=f"n_{index}")
        col_h1, col_h2 = st.columns(2)
        h_deb = col_h1.text_input("Début (ex: 11:15)", key=f"hd_{index}")
        h_fin = col_h2.text_input("Fin (ex: 13:00)", key=f"hf_{index}")
        
        if st.button("Confirmer la réservation", key=f"btn_{index}"):
            if nom_res and h_deb and h_fin:
                creneau_texte = f"{nom_res} ({h_deb}-{h_fin})"
                if "libre" in statut:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom_res, "debut": h_deb, "fin": h_fin, "suivant": row['Suivant']}
                else:
                    liste = f"{row['Suivant']} | {creneau_texte}" if row['Suivant'] else creneau_texte
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": row['Utilisateur'], "debut": row['Début'], "fin": row['Fin'], "suivant": liste}
                
                requests.post(SCRIPT_URL, json=payload)
                st.success("Planifié !"); st.rerun()

    if row['Suivant']:
        st.write("🗓 **File d'attente :**")
        for s in str(row['Suivant']).split(" | "):
            st.caption(f"• {s}")
    st.divider()
