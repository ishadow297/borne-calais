import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# --- CONFIGURATION (À REMPLIR) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")

# --- GESTION DU TEMPS ---
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)
heure_actuelle = now.strftime("%H:%M")

# --- LECTURE DU TABLEAU ---
try:
    # On force le rafraîchissement avec un paramètre nocache
    df = pd.read_csv(f"{SHEET_CSV}&v={now.microsecond}").fillna("")
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error("Erreur de lecture du Google Sheets. Vérifiez qu'il est bien 'Public'.")
    st.stop()

st.title("⚡ Planning des Bornes")
st.subheader(f"📍 Calais | 🕒 {heure_actuelle}")

# --- BOUCLE SUR CHAQUE BORNE ---
for index, row in df.iterrows():
    # Sécurité : on vérifie si les colonnes existent, sinon on met vide
    statut = str(row.get('Statut', 'Libre')).lower()
    user = row.get('Utilisateur', '')
    h_deb = row.get('Début', '')
    h_fin = row.get('Fin', '')
    file_attente = str(row.get('Suivant', ''))

    # Définition de la couleur
    bg_color = "#d4edda" # Vert (Libre)
    if "occupe" in statut: bg_color = "#f8d7da" # Rouge
    if "panne" in statut: bg_color = "#fff3cd" # Orange

    # --- AFFICHAGE DE LA CARTE ---
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{bg_color}; border:1px solid #ccc; margin-bottom:10px">
            <h3 style="margin:0">🔌 {row.get('Borne', 'Sans nom')}</h3>
            <p style="margin:0">📍 {row.get('Lieu', 'Calais')}</p>
            <hr style="margin:10px 0">
            <p style="margin:0"><b>Utilisateur :</b> {user if user else 'DISPONIBLE'}</p>
            <p style="margin:0">⌚ <b>Créneau :</b> {h_deb} {'à' if h_fin else ''} {h_fin}</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if "panne" in statut:
            if st.button(f"🔧 Borne Réparée", key=f"fix_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": file_attente}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()
        else:
            if st.button(f"🚩 Signaler Panne", key=f"p_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HORS SERVICE", "debut": "", "fin": "", "suivant": file_attente}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    with col2:
        if "occupe" in statut:
            if st.button(f"✅ Terminer / Suivant", key=f"lib_{index}"):
                # Gestion de la file d'attente
                suivants = file_attente.split(" | ") if file_attente else []
                suivants = [s for s in suivants if s.strip()]
                
                if suivants:
                    p_brut = suivants.pop(0) # ex: "Julien (14:00-15:00)"
                    try:
                        p_nom = p_brut.split(" (")[0]
                        p_h = p_brut.split(" (")[1].replace(")", "").split("-")
                        p_d, p_f = p_h[0], p_h[1]
                    except:
                        p_nom = p_brut; p_d = "En cours"; p_f = ""
                    
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": p_nom, "debut": p_d, "fin": p_f, "suivant": " | ".join(suivants)}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- FORMULAIRE RÉSERVATION ---
    with st.expander("📅 Réserver cette borne"):
        nom_res = st.text_input("Ton Prénom", key=f"n_{index}")
        c_h1, c_h2 = st.columns(2)
        h_d = c_h1.text_input("Début (ex: 11:30)", key=f"hd_{index}")
        h_f = c_h2.text_input("Fin (ex: 13:00)", key=f"hf_{index}")
        
        if st.button("Confirmer", key=f"btn_{index}"):
            if nom_res and h_d and h_f:
                creneau = f"{nom_res} ({h_d}-{h_f})"
                if "libre" in statut:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom_res, "debut": h_d, "fin": h_f, "suivant": file_attente}
                else:
                    nouvelle_file = f"{file_attente} | {creneau}" if file_attente else creneau
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": user, "debut": h_deb, "fin": h_fin, "suivant": nouvelle_file}
                
                requests.post(SCRIPT_URL, json=payload)
                st.success("Réservé !")
                st.rerun()

    if file_attente:
        st.caption(f"🗓 **File d'attente :** {file_attente}")
    st.divider()
