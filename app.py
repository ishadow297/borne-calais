import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz # Import indispensable pour l'heure française

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfr__TekrEpJGmVEu1SvGqRVIppFOQDQJ_MUp7_lwxSRDZ5NAFVlnoThtybQ7IuZlM/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/export?format=csv"

st.set_page_config(page_title="Planning Bornes Calais", page_icon="⚡")
st.title("⚡ Planning Intelligent Calais")

# --- RÉGLAGE DE L'HEURE (FRANCE - EUROPE/PARIS) ---
tz_france = pytz.timezone('Europe/Paris')
now = datetime.now(tz_france)

date_aujourdhui = now.strftime("%d/%m")
date_demain = (now + pd.Timedelta(days=1)).strftime("%d/%m")
heure_actuelle = now.strftime("%H:%M")

# Lecture du fichier
df = pd.read_csv(f"{SHEET_CSV}&cache={now.second}").fillna("")

# Affichage de la date confirmée
st.header(f"📅 Aujourd'hui : {date_aujourdhui} | 🕒 {heure_actuelle}")

# --- LOGIQUE DE NETTOYAGE AUTO ---
for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    borne_doit_etre_liberee = False

    if statut == "occupé":
        try:
            date_info = str(row['Heure de fin'])
            if " | " in date_info:
                jour_f, heures_f = date_info.split(" | ")
                _, h_fin = heures_f.split(" >> ")
                
                # Comparaison : si le jour est arrivé/passé ET l'heure est passée
                # Note: On transforme les dates en format comparable si besoin
                if jour_f == date_aujourdhui and heure_actuelle > h_fin:
                    borne_doit_etre_liberee = True
                elif jour_f < date_aujourdhui: # Si c'est un vieux reste d'hier
                    borne_doit_etre_liberee = True
        except:
            pass

    if borne_doit_etre_liberee:
        file = str(row['Suivant'])
        nouveau_statut, nouvel_user, nouvelle_heure, nouvelle_file = "libre", "", "", ""

        if file:
            resas = file.split(" | ")
            prochaine = resas[0].replace("• ", "")
            if "(" in prochaine:
                nouvel_user = prochaine.split(" (")[0]
                nouvelle_heure = prochaine.split("(")[1].replace(")", "")
                nouveau_statut = "Occupé"
                nouvelle_file = " | ".join(resas[1:])
        
        payload = {
            "row": index+1, "borne": row['Borne'], "statut": nouveau_statut,
            "utilisateur": nouvel_user, "heure": nouvelle_heure, "suivant": nouvelle_file
        }
        requests.post(SCRIPT_URL, json=payload)
        st.rerun()

    # --- AFFICHAGE ---
    with st.container(border=True):
        st.subheader(f"📍 {row['Borne']}")
        if statut == "occupé":
            st.write(f"🔴 **{row['Utilisateur']}** : {row['Heure de fin']}")
        else:
            st.write("✅ **Libre**")
        
        if row['Suivant']:
            st.info(f"⏳ **À venir :**\n\n{row['Suivant']}".replace(" | ", "\n\n"))

# --- FORMULAIRE DE RÉSERVATION ---
st.divider()
st.header("📅 Réserver un créneau")

with st.form("form_resa"):
    choix_borne = st.selectbox("Borne", df['Borne'].unique())
    choix_jour = st.radio("Jour", [f"Aujourd'hui ({date_aujourdhui})", f"Demain ({date_demain})"])
    nom = st.text_input("Ton prénom")
    
    heures_list = [f"{h:02d}:{m:02d}" for h in range(0, 24) for m in (0, 30)]
    c1, c2 = st.columns(2)
    h_start = c1.selectbox("Début", heures_list, index=16)
    h_end = c2.selectbox("Fin", heures_list, index=20)
    
    if st.form_submit_button("VALIDER LA RÉSERVATION"):
        if nom and h_start < h_end:
            idx = df[df['Borne'] == choix_borne].index[0]
            jour_f = choix_jour.split(" (")[1].replace(")", "")
            nouveau_creneau = f"{jour_f} | {h_start} >> {h_end}"
            
            file_actuelle = str(df.iloc[idx]['Suivant'])
            if str(df.iloc[idx]['Statut']).lower() == "libre":
                 payload = {"row": idx + 1, "borne": choix_borne, "statut": "Occupé", "utilisateur": nom, "heure": nouveau_creneau, "suivant": file_actuelle}
            else:
                info_resa = f"• {nom} ({nouveau_creneau})"
                nouvelle_file = f"{file_actuelle} | {info_resa}".strip(" | ")
                payload = {"row": idx + 1, "borne": choix_borne, "statut": df.iloc[idx]['Statut'], "utilisateur": df.iloc[idx]['Utilisateur'], "heure": df.iloc[idx]['Heure de fin'], "suivant": nouvelle_file}
            
            requests.post(SCRIPT_URL, json=payload)
            st.success("Réservation ajoutée !")
            st.rerun()
