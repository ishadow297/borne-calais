import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION (N'oublie pas ton URL de script) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfr__TekrEpJGmVEu1SvGqRVIppFOQDQJ_MUp7_lwxSRDZ5NAFVlnoThtybQ7IuZlM/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/export?format=csv"

st.set_page_config(page_title="Planning Bornes", page_icon="⚡")
st.title("⚡ Planning Bornes Calais")

# --- RÉGLAGE DE L'HEURE (FRANCE +2h) ---
# On ajuste ici pour qu'il soit bien 1h23 du matin si c'est l'heure chez toi
now = datetime.utcnow() + timedelta(hours=2) 
date_aujourdhui = now.strftime("%d/%m")
date_demain = (now + timedelta(days=1)).strftime("%d/%m")
heure_actuelle = now.strftime("%H:%M")

# Lecture du fichier
try:
    df = pd.read_csv(f"{SHEET_CSV}&cache={now.second}").fillna("")
except:
    st.error("Erreur de connexion au Sheets.")
    st.stop()

# --- AFFICHAGE DES BORNES ---
st.header(f"🕒 Il est {heure_actuelle} le {date_aujourdhui}")

for index, row in df.iterrows():
    borne_libre = True
    info_occupant = ""
    
    # On vérifie si une charge est en cours
    if str(row['Statut']).lower() == "occupé":
        try:
            # Format dans le Sheets : "JJ/MM | 08:00 >> 10:00"
            date_info = str(row['Heure de fin'])
            if " | " in date_info:
                jour_brut, heures_brut = date_info.split(" | ")
                h_debut, h_fin = heures_brut.split(" >> ")
                
                # Si c'est aujourd'hui et que l'heure de FIN est passée, on libère
                if jour_brut == date_aujourdhui and heure_actuelle > h_fin:
                    borne_libre = True
                else:
                    borne_libre = False
                    info_occupant = f"👤 **{row['Utilisateur']}** : {h_debut} à {h_fin} ({jour_brut})"
            else:
                borne_libre = False
        except:
            borne_libre = False

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            icon = "🟢" if borne_libre else "🔴"
            st.subheader(f"{icon} {row['Borne']}")
            st.write(info_occupant if not borne_libre else "✅ Disponible")
        
        with col2:
            if not borne_libre:
                if st.button("Libérer", key=f"lib_{index}"):
                    payload = {"row": index+1, "borne": row['Borne'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": ""}
                    requests.post(SCRIPT_URL, json=payload)
                    st.rerun()

# --- RÉSERVATION ---
st.divider()
st.header("📅 Réserver un créneau")

# Liste d'heures (00:00 à 23:30)
heures_list = [f"{h:02d}:{m:02d}" for h in range(0, 24) for m in (0, 30)]

with st.form("form_resa"):
    choix_borne = st.selectbox("Borne", df['Borne'].unique())
    choix_jour = st.radio("Jour", [f"Aujourd'hui ({date_aujourdhui})", f"Demain ({date_demain})"])
    nom = st.text_input("Ton prénom")
    
    c1, c2 = st.columns(2)
    h_start = c1.selectbox("Début de charge", heures_list, index=16) # Par défaut 08:00
    h_end = c2.selectbox("Fin de charge", heures_list, index=20)   # Par défaut 10:00
    
    if st.form_submit_button("VALIDER"):
        if nom and h_start < h_end:
            jour_final = choix_jour.split(" (")[1].replace(")", "")
            # On enregistre tout dans la colonne 'Heure de fin' pour le calcul
            format_sheets = f"{jour_final} | {h_start} >> {h_end}"
            
            idx = df[df['Borne'] == choix_borne].index[0]
            payload = {
                "row": idx + 1,
                "borne": choix_borne,
                "statut": "Occupé",
                "utilisateur": nom,
                "heure": format_sheets,
                "suivant": ""
            }
            requests.post(SCRIPT_URL, json=payload)
            st.success(f"Réservé ! {nom} de {h_start} à {h_end}")
            st.rerun()
        else:
            st.error("Vérifie ton nom ou l'heure (le début doit être avant la fin) !")
