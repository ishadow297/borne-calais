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

# --- LECTURE ---
try:
    # On ajoute un paramètre aléatoire pour éviter que Google garde en cache les vieilles données
    df = pd.read_csv(f"{SHEET_CSV}&nocache={now.microsecond}").fillna("")
    df.columns = df.columns.str.strip()
except:
    st.error("Erreur de connexion au tableur. Vérifie le partage public.")
    st.stop()

st.title("⚡ Réservation Bornes de Recharge")

for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    color = "#28a745" if "libre" in statut else "#dc3545"
    if "panne" in statut: color = "#ffc107"

    # Affichage du badge
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; border-left: 10px solid {color}; background:#f9f9f9; margin-bottom:10px">
            <h3 style="margin:0">{row['Borne']} <small>({row['Lieu']})</small></h3>
            <p style="margin:0"><b>Statut :</b> {statut.upper()} | <b>Actuel :</b> {row['Utilisateur'] or 'Personne'}</p>
            <p style="margin:0; font-size:0.8em">Fin prévue : {row['Heure de fin'] or '--:--'}</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    # --- BOUTON PANNE / RÉPARER ---
    with col1:
        if "panne" in statut:
            if st.button(f"🔧 Réparée", key=f"fix_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()
        else:
            if st.button(f"🚩 Panne", key=f"p_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HORS SERVICE", "heure": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- BOUTON LIBÉRER ---
    with col2:
        if "occupe" in statut:
            if st.button(f"✅ Libérer", key=f"lib_{index}"):
                # Si on libère, on regarde s'il y a quelqu'un après dans la colonne 'Suivant'
                suivants = str(row['Suivant']).split(" | ") if row['Suivant'] else []
                if suivants and suivants[0] != "":
                    prochain = suivants.pop(0) # On prend le premier de la liste
                    new_suivant = " | ".join(suivants)
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": prochain, "heure": "En cours", "suivant": new_suivant}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- FORMULAIRE DE RÉSERVATION ---
    with col3:
        with st.popover("📅 Réserver"):
            nom = st.text_input("Ton Nom", key=f"nom_{index}")
            h_fin = st.text_input("Heure de fin (ex: 14:30)", key=f"h_{index}")
            if st.button("Confirmer", key=f"conf_{index}"):
                if nom:
                    if "libre" in statut:
                        # Si libre, on occupe immédiatement
                        payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom, "heure": h_fin, "suivant": row['Suivant']}
                    else:
                        # Si déjà occupé, on ajoute à la file d'attente dans 'Suivant'
                        actuel_suivant = str(row['Suivant'])
                        file = f"{actuel_suivant} | {nom} ({h_fin})" if actuel_suivant else f"{nom} ({h_fin})"
                        payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": row['Utilisateur'], "heure": row['Heure de fin'], "suivant": file}
                    
                    requests.post(SCRIPT_URL, json=payload)
                    st.success("Réservé !")
                    st.rerun()

    # Affichage de la file d'attente
    if row['Suivant']:
        st.caption(f"⏳ File d'attente : {row['Suivant']}")
