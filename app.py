import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyHCSrzomz-6fnHUZNQ_6K6HI03OrH6DLHQeJJCDyGeQaUzK6Qcuvf3XPpxy1Upfj25/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais Pro", page_icon="⚡", layout="wide")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- FONCTION DE NETTOYAGE ET SYNCHRO ---
def sync_and_clean():
    url = f"{SHEET_CSV}&v={time.time()}"
    df_raw = pd.read_csv(url).fillna("")
    df_raw.columns = df_raw.columns.str.strip()
    
    for i, row in df_raw.iterrows():
        needs_update = False
        file_attente = str(row['Suivant']).strip()
        
        # 1. Vérifier si l'utilisateur ACTUEL a fini son temps
        if row['Statut'].lower() == "occupé" and row['Fin']:
            try:
                h_fin = datetime.strptime(row['Fin'], "%H:%M").time()
                dt_fin = datetime.combine(now.date(), h_fin).replace(tzinfo=tz)
                
                if now > dt_fin:
                    needs_update = True
                    # On passe au suivant ou on libère
                    if file_attente and file_attente.lower() != "nan":
                        items = file_attente.split(" | ")
                        next_up = items.pop(0)
                        p_nom = next_up.split(" [")[0]
                        p_times = next_up.split(" ")[2].replace("]", "").split("-")
                        
                        row['Utilisateur'], row['Début'], row['Fin'] = p_nom, p_times[0], p_times[1]
                        row['Suivant'] = " | ".join(items)
                    else:
                        row['Statut'], row['Utilisateur'], row['Début'], row['Fin'], row['Suivant'] = "libre", "", "", "", ""
            except: pass

        # 2. Nettoyer les réservations périmées dans la FILE D'ATTENTE
        if file_attente and file_attente.lower() != "nan":
            items = file_attente.split(" | ")
            valid_items = []
            for item in items:
                try:
                    # Format: Nom [DD/MM HH:MM-HH:MM]
                    date_info = item.split("[")[1].split("]")[0]
                    day_month = date_info.split(" ")[0]
                    end_hour = date_info.split(" ")[1].split("-")[1]
                    
                    dt_item_fin = datetime.strptime(f"{day_month}/{now.year} {end_hour}", "%d/%m/%Y %H:%M").replace(tzinfo=tz)
                    if dt_item_fin > now:
                        valid_items.append(item)
                    else:
                        needs_update = True # On a trouvé un vieux créneau, on devra mettre à jour le Sheets
                except:
                    valid_items.append(item) # En cas de doute, on garde
            
            row['Suivant'] = " | ".join(valid_items)

        # 3. Envoyer la mise à jour au Sheets si un changement a eu lieu
        if needs_update:
            p = {
                "row": i+1, "borne": row['Borne'], "lieu": row['Lieu'], 
                "statut": row['Statut'], "utilisateur": row['Utilisateur'], 
                "debut": row['Début'], "fin": row['Fin'], "suivant": row['Suivant']
            }
            requests.post(SCRIPT_URL, json=p)
            time.sleep(0.5) # Petit délai pour laisser Google respirer

    return df_raw

# Exécuter la synchro au chargement
df = sync_and_clean()

# --- INTERFACE ---
st.title("⚡ Bornes de Recharge Calais")
st.info(f"🕒 Heure actuelle : **{now.strftime('%H:%M')}** - Les créneaux passés sont automatiquement supprimés.")

# Liste des heures pour le calendrier
heures_list = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]

for index, row in df.iterrows():
    borne = str(row['Borne'])
    statut = str(row['Statut']).lower()
    file_attente = str(row['Suivant']).strip()
    
    # Couleur et design
    color = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: color = "#fff3cd"

    st.markdown(f"""
        <div style="padding:20px; border-radius:15px; background:{color}; border:2px solid #bbb; color:black; margin-bottom:10px">
            <h2 style="margin:0">📍 {borne}</h2>
            <p style="font-size:1.2em; margin:5px 0"><b>Actuel :</b> {row['Utilisateur'] if row['Utilisateur'] else 'LIBRE'}</p>
            <p style="margin:0"><b>Créneau :</b> {row['Début']} ⮕ {row['Fin'] if row['Fin'] else '---'}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        # Bouton Panne
        label_p = "🔧 Marquer Réparée" if "panne" in statut else "🚩 Signaler Panne"
        if st.button(label_p, key=f"p_{index}", use_container_width=True):
            p = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "libre" if "panne" in statut else "panne", "utilisateur": "", "debut": "", "fin": "", "suivant": file_attente}
            requests.post(SCRIPT_URL, json=p)
            st.rerun()
    with c2:
        # Bouton Terminer
        if "occupé" in statut:
            if st.button("✅ Terminer / Suivant", key=f"l_{index}", use_container_width=True):
                items = [i.strip() for i in file_attente.split("|") if i.strip()]
                if items:
                    n = items.pop(0)
                    p_nom = n.split(" [")[0]
                    p_c = n.split(" ")[2].replace("]", "").split("-")
                    p = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "occupé", "utilisateur": p_nom, "debut": p_c[0], "fin": p_c[1], "suivant": "|".join(items)}
                else:
                    p = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=p)
                st.rerun()

    # Formulaire de réservation
    with st.expander("📅 Réserver un créneau futur"):
        with st.form(key=f"f_{index}"):
            f_nom = st.text_input("Prénom")
            f_date = st.date_input("Date", value=now.date(), min_value=now.date())
            col_h1, col_h2 = st.columns(2)
            f_deb = col_h1.selectbox("Début", heures_list, index=20)
            f_fin = col_h2.selectbox("Fin", heures_list, index=24)
            if st.form_submit_button("Valider la réservation"):
                if f_nom:
                    d_txt = f_date.strftime("%d/%m")
                    nouvelle_resa = f"{f_nom} [{d_txt} {f_deb}-{f_fin}]"
                    if "libre" in statut and f_date == now.date():
                        p = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": "occupé", "utilisateur": f_nom, "debut": f_deb, "fin": f_fin, "suivant": file_attente}
                    else:
                        file_maj = f"{file_attente} | {nouvelle_resa}" if (file_attente and file_attente != "nan") else nouvelle_resa
                        p = {"row": index+1, "borne": borne, "lieu": row['Lieu'], "statut": statut, "utilisateur": row['Utilisateur'], "debut": row['Début'], "fin": row['Fin'], "suivant": file_maj}
                    requests.post(SCRIPT_URL, json=p)
                    st.rerun()

    if file_attente and file_attente != "nan":
        st.write("📋 **Planning :**")
        for r in file_attente.split("|"):
            st.caption(f"• {r.strip()}")
    st.divider()
