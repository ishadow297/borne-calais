import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfr__TekrEpJGmVEu1SvGqRVIppFOQDQJ_MUp7_lwxSRDZ5NAFVlnoThtybQ7IuZlM/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/export?format=csv"

st.set_page_config(page_title="Planning Bornes", page_icon="⚡")
st.title("⚡ Planning Bornes Calais")

# --- RÉGLAGE DE L'HEURE (FRANCE +2h) ---
now = datetime.utcnow() + timedelta(hours=2) 
date_aujourdhui = now.strftime("%d/%m")
date_demain = (now + timedelta(days=1)).strftime("%d/%m")
heure_actuelle = now.strftime("%H:%M")

# Lecture du fichier
df = pd.read_csv(f"{SHEET_CSV}&cache={now.second}").fillna("")

st.header(f"🕒 Il est {heure_actuelle} (le {date_aujourdhui})")

# --- AFFICHAGE DES BORNES ---
for index, row in df.iterrows():
    # On regarde si quelqu'un est branché maintenant
    occupant_actuel = "✅ Libre"
    statut_brut = str(row['Statut']).lower()
    
    if statut_brut == "occupé":
        occupant_actuel = f"🔴 **{row['Utilisateur']}** : {row['Heure de fin']}"

    with st.container(border=True):
        st.subheader(f"📍 {row['Borne']}")
        st.write(f"**État actuel :** {occupant_actuel}")
        
        # Affichage de la liste d'attente / Réservations futures
        if row['Suivant']:
            st.info(f"📅 **Réservations à venir :**\n\n{row['Suivant']}".replace(" | ", "\n\n"))
        
        if st.button(f"🗑️ TOUT VIDER (Borne {row['Borne']})", key=f"clr_{index}"):
            payload = {"row": index+1, "borne": row['Borne'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": ""}
            requests.post(SCRIPT_URL, json=payload)
            st.rerun()

# --- FORMULAIRE DE RÉSERVATION ---
st.divider()
st.header("📅 Réserver un créneau")

with st.form("form_resa"):
    choix_borne = st.selectbox("Choisir la borne", df['Borne'].unique())
    choix_jour = st.radio("Pour quand ?", [f"Aujourd'hui ({date_aujourdhui})", f"Demain ({date_demain})"])
    nom = st.text_input("Ton prénom")
    
    heures_list = [f"{h:02d}:{m:02d}" for h in range(0, 24) for m in (0, 30)]
    c1, c2 = st.columns(2)
    h_start = c1.selectbox("Début", heures_list, index=16)
    h_end = c2.selectbox("Fin", heures_list, index=20)
    
    # L'UTILISATEUR CHOISIT SI IL ÉCRASE OU SI IL AJOUTE
    mode = st.radio("Action :", ["Je me branche MAINTENANT (Remplace l'actuel)", "Je réserve pour PLUS TARD (Ajoute à la liste)"])
    
    if st.form_submit_button("VALIDER"):
        if nom and h_start < h_end:
            idx = df[df['Borne'] == choix_borne].index[0]
            jour_final = choix_jour.split(" (")[1].replace(")", "")
            nouveau_creneau = f"{jour_final} | {h_start} >> {h_end}"
            
            if mode == "Je me branche MAINTENANT (Remplace l'actuel)":
                # On remplace l'occupant principal mais on GARDE la liste d'attente
                payload = {
                    "row": idx + 1, "borne": choix_borne, "statut": "Occupé",
                    "utilisateur": nom, "heure": nouveau_creneau, "suivant": df.iloc[idx]['Suivant']
                }
            else:
                # On ne touche pas à l'actuel, on ajoute seulement dans 'suivant'
                file_actuelle = str(df.iloc[idx]['Suivant'])
                info_resa = f"• {nom} ({nouveau_creneau})"
                # On empile les réservations
                nouvelle_file = f"{file_actuelle} | {info_resa}".strip(" | ")
                
                payload = {
                    "row": idx + 1, "borne": choix_borne, "statut": df.iloc[idx]['Statut'],
                    "utilisateur": df.iloc[idx]['Utilisateur'], "heure": df.iloc[idx]['Heure de fin'],
                    "suivant": nouvelle_file
                }
            
            requests.post(SCRIPT_URL, json=payload)
            st.success("C'est enregistré !")
            st.rerun()
