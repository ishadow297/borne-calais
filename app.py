import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais Pro", page_icon="⚡")

# --- GESTION DU TEMPS ---
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LECTURE ET NETTOYAGE AUTOMATIQUE ---
try:
    url_refresh = f"{SHEET_CSV}&v={now.timestamp()}"
    df = pd.read_csv(url_refresh).fillna("")
    df.columns = df.columns.str.strip()
    
    # Logique de nettoyage : Si l'heure de fin est passée, on libère la borne
    # (Note: Cette partie nécessite que l'utilisateur clique sur "Libérer" pour être précis, 
    # mais on peut forcer le statut libre si on détecte un retard important)
except Exception as e:
    st.error("Erreur de lecture.")
    st.stop()

st.title("⚡ Planning Long Terme")
st.info(f"📅 Nous sommes le **{now.strftime('%d/%m/%Y')}** | 🕒 **{now.strftime('%H:%M')}**")

for index, row in df.iterrows():
    statut = str(row.get('Statut', 'Libre')).lower()
    file_attente = str(row.get('Suivant', ''))
    
    # Couleur selon l'état
    bg = "#d4edda" if "libre" in statut else "#f8d7da"
    if "panne" in statut: bg = "#fff3cd"

    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{bg}; border:1px solid #ccc; margin-bottom:10px; color:black">
            <h3 style="margin:0">🔌 {row['Borne']}</h3>
            <p style="margin:0"><b>Actuel :</b> {row['Utilisateur'] if row['Utilisateur'] else 'Libre'}</p>
            <p style="margin:0"><b>Fin :</b> {row['Fin'] if row['Fin'] else '--:--'}</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if "panne" in statut:
            if st.button(f"🔧 Réparée", key=f"fix_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": file_attente}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()
        else:
            if st.button(f"🚩 Panne", key=f"p_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HS", "debut": "", "fin": "", "suivant": file_attente}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    with col2:
        if "occupe" in statut:
            if st.button(f"✅ Terminer / Suivant", key=f"lib_{index}"):
                suivants = [s.strip() for s in file_attente.split("|") if s.strip()]
                if suivants:
                    prochain = suivants.pop(0) # On récupère le premier de la liste
                    # Format attendu : "Nom (Date HeureFin)"
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": prochain, "debut": "Pris", "fin": "Voir file", "suivant": "|".join(suivants)}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- FORMULAIRE LONG TERME ---
    with st.expander("📅 Réserver (Aujourd'hui ou Futur)"):
        with st.form(key=f"form_{index}"):
            res_nom = st.text_input("Nom / Prénom")
            res_date = st.date_input("Date", value=now.date())
            res_heure = st.text_input("Heure de fin (ex: 17:30)")
            submit = st.form_submit_button("Ajouter à la suite")
            
            if submit and res_nom and res_heure:
                info_res = f"{res_nom} [{res_date.strftime('%d/%m')} à {res_heure}]"
                
                # SI LIBRE : On prend la place tout de suite
                if "libre" in statut:
                    new_payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": res_nom, "debut": "Maintenant", "fin": f"{res_date.strftime('%d/%m')} {res_heure}", "suivant": file_attente}
                # SI OCCUPÉ : On ajoute à la file sans écraser
                else:
                    nouvelle_file = f"{file_attente} | {info_res}" if file_attente else info_res
                    new_payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": row['Utilisateur'], "debut": row['Début'], "fin": row['Fin'], "suivant": nouvelle_file}
                
                requests.post(SCRIPT_URL, json=new_payload)
                st.success("Ajouté au planning !")
                time.sleep(1)
                st.rerun()

    if file_attente:
        st.write("📋 **Planning à venir :**")
        for i, resa in enumerate(file_attente.split("|")):
            st.caption(f"{i+1}. {resa}")
    st.divider()
