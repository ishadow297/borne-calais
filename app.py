import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
# Remplacez par votre nouvelle URL de déploiement (le lien /exec)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡", layout="centered")

# --- GESTION DU TEMPS ET ANTI-CACHE ---
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)
timestamp = now.timestamp() # Pour forcer Google à rafraîchir

# --- LECTURE DES DONNÉES ---
try:
    # On ajoute le timestamp à l'URL pour éviter le cache de 5min de Google
    url_refresh = f"{SHEET_CSV}&v={timestamp}"
    df = pd.read_csv(url_refresh).fillna("")
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error("⚠️ Erreur de connexion au Google Sheets.")
    st.stop()

# --- INTERFACE ---
st.title("⚡ Bornes de Recharge Calais")
st.info(f"🕒 Heure actuelle : **{now.strftime('%H:%M')}**")

# --- BOUCLE D'AFFICHAGE ---
for index, row in df.iterrows():
    statut = str(row.get('Statut', 'Libre')).lower()
    user = row.get('Utilisateur', '')
    h_deb = row.get('Début', '')
    h_fin = row.get('Fin', '')
    file_attente = str(row.get('Suivant', ''))

    # Couleur de la carte
    bg_color = "#d4edda" # Vert
    if "occupe" in statut: bg_color = "#f8d7da" # Rouge
    if "panne" in statut: bg_color = "#fff3cd" # Orange

    # Affichage visuel
    st.markdown(f"""
        <div style="padding:20px; border-radius:15px; background:{bg_color}; border:1px solid #ddd; margin-bottom:10px; color:black">
            <h2 style="margin:0">🔌 {row['Borne']}</h2>
            <p style="margin:0; opacity:0.8">📍 {row['Lieu']}</p>
            <hr style="border:0.5px solid #bbb">
            <p style="margin:0; font-size:1.1em"><b>Utilisateur :</b> {user if user else 'LIBRE'}</p>
            <p style="margin:0; font-size:1.1em"><b>⌚ Créneau :</b> {h_deb} {'à' if h_fin else ''} {h_fin}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        # Gestion Panne / Réparation
        if "panne" in statut:
            if st.button(f"🔧 Borne Réparée", key=f"fix_{index}", use_container_width=True):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": file_attente}
                requests.post(SCRIPT_URL, json=payload)
                with st.spinner("Mise à jour..."): time.sleep(1.5)
                st.rerun()
        else:
            if st.button(f"🚩 Signaler Panne", key=f"p_{index}", use_container_width=True):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HORS SERVICE", "debut": "", "fin": "", "suivant": file_attente}
                requests.post(SCRIPT_URL, json=payload)
                with st.spinner("Mise à jour..."): time.sleep(1.5)
                st.rerun()

    with c2:
        # Libérer ou passer au suivant
        if "occupe" in statut:
            if st.button(f"✅ Terminer / Suivant", key=f"lib_{index}", use_container_width=True):
                suivants = file_attente.split(" | ") if file_attente else []
                suivants = [s for s in suivants if s.strip()]
                
                if suivants:
                    p_brut = suivants.pop(0) # ex: "Jean (14:00-15:00)"
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
                with st.spinner("Passage au suivant..."): time.sleep(1.5)
                st.rerun()

    # Formulaire de réservation
    with st.expander(f"📅 Réserver un créneau sur {row['Borne']}"):
        nom_res = st.text_input("Prénom", key=f"n_{index}")
        ch1, ch2 = st.columns(2)
        h_d = ch1.text_input("Début (ex: 11:30)", key=f"hd_{index}")
        h_f = ch2.text_input("Fin (ex: 13:00)", key=f"hf_{index}")
        
        if st.button("Confirmer la réservation", key=f"btn_{index}"):
            if nom_res and h_d and h_f:
                creneau = f"{nom_res} ({h_d}-{h_f})"
                if "libre" in statut:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom_res, "debut": h_d, "fin": h_f, "suivant": file_attente}
                else:
                    nouvelle_file = f"{file_attente} | {creneau}" if file_attente else creneau
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": user, "debut": h_deb, "fin": h_fin, "suivant": nouvelle_file}
                
                requests.post(SCRIPT_URL, json=payload)
                st.success(f"Réservé pour {nom_res} !")
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning("Veuillez remplir tous les champs.")

    if file_attente:
        st.markdown(f"🗓 **File d'attente :** `{file_attente}`")
    st.divider()
