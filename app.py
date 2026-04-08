import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION (N'oublie pas ton URL) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfr__TekrEpJGmVEu1SvGqRVIppFOQDQJ_MUp7_lwxSRDZ5NAFVlnoThtybQ7IuZlM/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/export?format=csv"

st.set_page_config(page_title="Planning Bornes", page_icon="⚡")
st.title("⚡ Planning Auto-Géré")

# --- GESTION DU TEMPS ---
# On récupère la date et l'heure actuelle (France)
now = datetime.now() + timedelta(hours=0) # Ajuste à +1 ou +2 si l'heure est décalée
date_aujourdhui = now.strftime("%d/%m")
date_demain = (now + timedelta(days=1)).strftime("%d/%m")

# Lecture du fichier
df = pd.read_csv(SHEET_CSV).fillna("")

# --- AFFICHAGE DES BORNES ---
st.header(f"📅 Aujourd'hui, le {date_aujourdhui}")

for index, row in df.iterrows():
    # On vérifie si la borne est périmée (Heure de fin passée le même jour)
    borne_libre = True
    info_occupant = ""
    
    if str(row['Statut']).lower() == "occupé":
        # Format attendu dans le Sheets pour l'heure de fin : "Jour - HH:MM"
        try:
            date_fin_str = str(row['Heure de fin']) # ex: "09/04 - 14:00"
            if " - " in date_fin_str:
                jour_fin, heure_fin = date_fin_str.split(" - ")
                
                # Si c'est aujourd'hui et que l'heure est passée, on libère
                if jour_fin == date_aujourdhui and now.strftime("%H:%M") > heure_fin:
                    borne_libre = True
                else:
                    borne_libre = False
                    info_occupant = f"👤 {row['Utilisateur']} jusqu'à {heure_fin} ({jour_fin})"
            else:
                borne_libre = False # Sécurité pour le texte libre
        except:
            borne_libre = False

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            icon = "🟢" if borne_libre else "🔴"
            st.subheader(f"{icon} {row['Borne']}")
            st.write(info_occupant if not borne_libre else "✅ Libre")
        
        with col2:
            if not borne_libre:
                if st.button("Libérer", key=f"lib_{index}"):
                    payload = {"row": index+1, "borne": row['Borne'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": ""}
                    requests.post(SCRIPT_URL, json=payload)
                    st.rerun()

# --- RÉSERVATION (CRENEAUX) ---
st.divider()
st.header("📅 Réserver un créneau")

with st.form("form_resa"):
    choix_borne = st.selectbox("Quelle borne ?", df['Borne'].unique())
    choix_jour = st.radio("Quel jour ?", [f"Aujourd'hui ({date_aujourdhui})", f"Demain ({date_demain})"])
    nom = st.text_input("Ton prénom")
    
    # Génération d'une liste d'heures (07:00 à 22:00)
    heures_list = [f"{h:02d}:00" for h in range(7, 23)] + [f"{h:02d}:30" for h in range(7, 23)]
    heures_list.sort()
    choix_heure = st.selectbox("Heure de FIN de charge", heures_list)
    
    if st.form_submit_button("VALIDER LA RÉSERVATION"):
        if nom:
            # On extrait juste la date "JJ/MM"
            jour_final = choix_jour.split(" (")[1].replace(")", "")
            heure_finale = f"{jour_final} - {choix_heure}"
            
            idx = df[df['Borne'] == choix_borne].index[0]
            payload = {
                "row": idx + 1,
                "borne": choix_borne,
                "statut": "Occupé",
                "utilisateur": nom,
                "heure": heure_finale,
                "suivant": ""
            }
            requests.post(SCRIPT_URL, json=payload)
            st.success(f"Réservé pour {nom} jusqu'à {choix_heure} le {jour_final}")
            st.rerun()
