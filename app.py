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

st.header(f"🕒 Il est {heure_actuelle} le {date_aujourdhui}")

# --- AFFICHAGE DES BORNES ---
for index, row in df.iterrows():
    borne_libre = True
    occupant_actuel = ""
    
    # 1. Vérification de l'occupant principal
    if str(row['Statut']).lower() == "occupé":
        try:
            date_info = str(row['Heure de fin'])
            if " | " in date_info:
                jour_brut, heures_brut = date_info.split(" | ")
                h_start, h_fin = heures_brut.split(" >> ")
                
                # Si c'est aujourd'hui et que l'heure de fin est passée, on libère l'affichage
                if jour_brut == date_aujourdhui and heure_actuelle > h_fin:
                    borne_libre = True
                else:
                    borne_libre = False
                    occupant_actuel = f"👤 **{row['Utilisateur']}** : {h_start} à {h_fin} ({jour_brut})"
        except:
            borne_libre = False

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"{'🟢' if borne_libre else '🔴'} {row['Borne']}")
            st.write(occupant_actuel if not borne_libre else "✅ Disponible maintenant")
            
            # 2. Affichage de la LISTE D'ATTENTE (les réservations suivantes)
            if row['Suivant']:
                st.info(f"📅 **Réservations suivantes :**\n{row['Suivant']}".replace(" | ", "\n"))
        
        with col2:
            if st.button("Tout libérer / Vider", key=f"clear_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

# --- FORMULAIRE DE RÉSERVATION ---
st.divider()
st.header("📅 Ajouter une réservation")

with st.form("form_resa"):
    choix_borne = st.selectbox("Borne", df['Borne'].unique())
    choix_jour = st.radio("Jour", [f"Aujourd'hui ({date_aujourdhui})", f"Demain ({date_demain})"])
    nom = st.text_input("Ton prénom")
    
    heures_list = [f"{h:02d}:{m:02d}" for h in range(0, 24) for m in (0, 30)]
    c1, c2 = st.columns(2)
    h_start = c1.selectbox("Début", heures_list, index=16)
    h_end = c2.selectbox("Fin", heures_list, index=20)
    
    if st.form_submit_button("VALIDER"):
        if nom and h_start < h_end:
            idx = df[df['Borne'] == choix_borne].index[0]
            jour_final = choix_jour.split(" (")[1].replace(")", "")
            nouveau_creneau = f"{jour_final} | {h_start} >> {h_end}"
            
            # SI LA BORNE EST LIBRE : On l'occupe directement
            if str(df.iloc[idx]['Statut']).lower() == "libre" or borne_libre:
                payload = {
                    "row": idx + 1, "borne": choix_borne, "statut": "Occupé",
                    "utilisateur": nom, "heure": nouveau_creneau, "suivant": df.iloc[idx]['Suivant']
                }
            # SI DÉJÀ OCCUPÉE : On l'ajoute à la colonne 'Suivant' (file d'attente)
            else:
                file_actuelle = str(df.iloc[idx]['Suivant'])
                info_resa = f"• {nom} ({nouveau_creneau})"
                nouvelle_file = f"{file_actuelle} | {info_resa}".strip(" | ")
                
                payload = {
                    "row": idx + 1, "borne": choix_borne, "statut": df.iloc[idx]['Statut'],
                    "utilisateur": df.iloc[idx]['Utilisateur'], "heure": df.iloc[idx]['Heure de fin'],
                    "suivant": nouvelle_file
                }
            
            requests.post(SCRIPT_URL, json=payload)
            st.success("Réservation ajoutée à la liste !")
            st.rerun()
