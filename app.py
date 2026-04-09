import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyHCSrzomz-6fnHUZNQ_6K6HI03OrH6DLHQeJJCDyGeQaUzK6Qcuvf3XPpxy1Upfj25/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Gestion Bornes Calais", page_icon="⚡", layout="wide")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- FONCTION DE NETTOYAGE ET PASSAGE DE RELAIS ---
def orchestrateur_donnees(df):
    for i, row in df.iterrows():
        # 1. Vérifier si la session actuelle est terminée
        if row['Statut'].lower() == "occupé" and row['Fin']:
            try:
                # On compare l'heure de fin avec maintenant
                h_fin = datetime.strptime(row['Fin'], "%H:%M").time()
                dt_fin = datetime.combine(now.date(), h_fin).replace(tzinfo=tz)
                
                if now > dt_fin:
                    # C'est fini ! On regarde s'il y a un suivant
                    file = str(row['Suivant']).strip()
                    if file and file.lower() != "nan":
                        items = file.split(" | ")
                        prochain = items.pop(0)
                        # Format: Nom [Date Heure-Heure]
                        p_nom = prochain.split(" [")[0]
                        p_creneau = prochain.split(" ")[2].replace("]", "").split("-")
                        
                        # On met à jour le DF localement (le push vers Google se fera au prochain clic)
                        df.at[i, 'Utilisateur'] = p_nom
                        df.at[i, 'Début'] = p_creneau[0]
                        df.at[i, 'Fin'] = p_creneau[1]
                        df.at[i, 'Suivant'] = " | ".join(items)
                    else:
                        df.at[i, 'Statut'] = "libre"
                        df.at[i, 'Utilisateur'] = ""
                        df.at[i, 'Début'] = ""
                        df.at[i, 'Fin'] = ""
            except: pass
    return df

# --- CHARGEMENT ---
try:
    raw_df = pd.read_csv(f"{SHEET_CSV}&v={time.time()}").fillna("")
    raw_df.columns = raw_df.columns.str.strip()
    df = orchestrateur_donnees(raw_df)
except:
    st.error("Erreur de connexion aux données.")
    st.stop()

# --- INTERFACE ---
st.title("⚡ Réseau de Bornes Électriques - Calais")
st.write(f"📅 **{now.strftime('%A %d %B')}** | 🕒 **{now.strftime('%H:%M')}**")

# Génération des options d'heures (08:00, 08:30, etc.)
heures_dispo = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]

for index, row in df.iterrows():
    # Variables
    borne = row['Borne']
    statut = row['Statut'].lower()
    file = str(row['Suivant']).strip()
    
    # Design des colonnes
    with st.container():
        col_info, col_action = st.columns([2, 1])
        
        with col_info:
            if "panne" in statut:
                st.error(f"❌ **{borne}** : HORS SERVICE")
            elif "occupé" in statut:
                st.warning(f"⏳ **{borne}** : Occupée par **{row['Utilisateur']}** jusqu'à **{row['Fin']}**")
            else:
                st.success(f"✅ **{borne}** : Disponible immédiatement")
            
            if file and file.lower() != "nan":
                st.caption(f"📅 À venir : {file}")

        with col_action:
            # Créer un menu déroulant pour les actions
            with st.popover("⚙️ Gérer la borne"):
                if "panne" in statut:
                    if st.button("🔧 Marquer comme Réparée", key=f"fix_{index}"):
                        p = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": file}
                        requests.post(SCRIPT_URL, json=p)
                        st.rerun()
                else:
                    if st.button("🚩 Signaler une Panne", key=f"hs_{index}"):
                        p = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HORS SERVICE", "debut": "", "fin": "", "suivant": file}
                        requests.post(SCRIPT_URL, json=p)
                        st.rerun()
                    
                    if "occupé" in statut:
                        if st.button("✅ Terminer la session", key=f"end_{index}"):
                            # Forcer le passage au suivant
                            items = [i.strip() for i in file.split("|") if i.strip()]
                            if items:
                                n = items.pop(0)
                                p_nom = n.split(" [")[0]
                                p_c = n.split(" ")[2].replace("]", "").split("-")
                                payload = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "occupé", "utilisateur": p_nom, "debut": p_c[0], "fin": p_c[1], "suivant": "|".join(items)}
                            else:
                                payload = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                            requests.post(SCRIPT_URL, json=payload)
                            st.rerun()

        # --- FORMULAIRE RÉSERVATION PRO ---
        with st.expander("📝 Réserver un créneau"):
            with st.form(key=f"form_{index}"):
                nom = st.text_input("Votre Prénom")
                date_res = st.date_input("Date", value=now.date(), min_value=now.date())
                c_h1, c_h2 = st.columns(2)
                h_start = c_h1.selectbox("Début", heures_dispo, index=20) # Défaut 10:00
                h_end = c_h2.selectbox("Fin", heures_dispo, index=24)   # Défaut 12:00
                
                if st.form_submit_button("Confirmer la réservation"):
                    if nom:
                        new_res = f"{nom} [{date_res.strftime('%d/%m')} {h_start}-{h_end}]"
                        
                        if statut == "libre" and date_res == now.date():
                            payload = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom, "debut": h_start, "fin": h_end, "suivant": file}
                        else:
                            f_maj = f"{file} | {new_res}" if (file and file != "nan") else new_res
                            payload = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": statut, "utilisateur": row['Utilisateur'], "debut": row['Début'], "fin": row['Fin'], "suivant": f_maj}
                        
                        requests.post(SCRIPT_URL, json=payload)
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
    st.divider()
