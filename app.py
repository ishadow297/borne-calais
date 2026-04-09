import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
# REMPLACE PAR TON URL /EXEC
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyFzgdMMbjg4SDcd5iQitC2ncBqgb0qcjIlioHavIOT4N-jbNIyaT0oydmc2JOroQGF/exec"
# TON LIEN CSV (PUBLIÉ SUR LE WEB)
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡", layout="centered")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- FONCTION DE LECTURE (SÉCURISÉE) ---
def get_data():
    # Le paramètre cachebuster force Google à donner la version réelle
    url = f"{SHEET_CSV}&cachebuster={time.time()}"
    df = pd.read_csv(url).fillna("")
    df.columns = df.columns.str.strip()
    return df

df = get_data()

st.title("⚡ Bornes de Recharge Calais")
st.subheader(f"🕒 {now.strftime('%H:%M')} — {now.strftime('%d/%m/%Y')}")

for index, row in df.iterrows():
    # Données actuelles de la ligne
    b_nom = str(row['Borne'])
    b_lieu = str(row['Lieu'])
    b_statut = str(row['Statut']).lower()
    b_user = str(row['Utilisateur'])
    b_deb = str(row['Début'])
    b_fin = str(row['Fin'])
    b_file = str(row['Suivant']).strip()
    if b_file.lower() == "nan": b_file = ""

    # Couleur
    bg_color = "#d4edda" if "libre" in b_statut else "#f8d7da"
    if "panne" in b_statut: bg_color = "#fff3cd"

    # Affichage Carte
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{bg_color}; border:2px solid #bbb; color:black; margin-bottom:10px">
            <h3 style="margin:0">🔌 {b_nom}</h3>
            <p style="margin:0">📍 {b_lieu}</p>
            <hr style="margin:10px 0">
            <p style="margin:0"><b>Utilisateur :</b> {b_user if b_user else 'DISPONIBLE'}</p>
            <p style="margin:0"><b>Session :</b> {b_deb} ⮕ {b_fin}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    
    with c1:
        # BOUTON PANNE
        btn_txt = "🔧 Réparée" if "panne" in b_statut else "🚩 Panne"
        if st.button(btn_txt, key=f"panne_{index}", use_container_width=True):
            new_statut = "libre" if "panne" in b_statut else "panne"
            payload = {"row": index+1, "borne": b_nom, "lieu": b_lieu, "statut": new_statut, "utilisateur": "", "debut": "", "fin": "", "suivant": b_file}
            requests.post(SCRIPT_URL, json=payload)
            st.rerun()

    with c2:
        # BOUTON LIBÉRER / SUIVANT
        if "occupe" in b_statut:
            if st.button("✅ Terminer", key=f"lib_{index}", use_container_width=True):
                file_items = [i.strip() for i in b_file.split("|") if i.strip()]
                if file_items:
                    prochain_brut = file_items.pop(0)
                    # On nettoie le texte pour l'affichage (ex: "Julien [10/04 12:00-14:00]")
                    p_nom = prochain_brut.split(" [")[0]
                    p_creneau = prochain_brut.split("[")[1].replace("]", "").split(" ")[1] if "[" in prochain_brut else "En cours"
                    p_debut, p_fin = p_creneau.split("-") if "-" in p_creneau else ("Auto", "Auto")
                    
                    payload = {"row": index+1, "borne": b_nom, "lieu": b_lieu, "statut": "occupé", "utilisateur": p_nom, "debut": p_debut, "fin": p_fin, "suivant": "|".join(file_items)}
                else:
                    payload = {"row": index+1, "borne": b_nom, "lieu": b_lieu, "statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # FORMULAIRE RÉSERVATION
    with st.expander("📅 Réserver un créneau"):
        with st.form(key=f"res_{index}", clear_on_submit=True):
            f_nom = st.text_input("Ton Prénom")
            f_date = st.date_input("Date", value=now.date())
            f_h_d = st.text_input("Heure de début (ex: 10:00)")
            f_h_f = st.text_input("Heure de fin (ex: 12:30)")
            
            if st.form_submit_button("Confirmer la réservation"):
                if f_nom and f_h_d and f_h_f:
                    # Création du texte de réservation
                    new_entry = f"{f_nom} [{f_date.strftime('%d/%m')} {f_h_d}-{f_h_f}]"
                    
                    # LOGIQUE SÉCURISÉE : On ne remplace JAMAIS b_file
                    if "libre" in b_statut and f_date == now.date():
                        # Cas direct : Libre aujourd'hui
                        payload = {"row": index+1, "borne": b_nom, "lieu": b_lieu, "statut": "occupé", "utilisateur": f_nom, "debut": f_h_d, "fin": f_h_f, "suivant": b_file}
                    else:
                        # Cas file d'attente : On concatène
                        updated_file = f"{b_file} | {new_entry}" if b_file else new_entry
                        payload = {"row": index+1, "borne": b_nom, "lieu": b_lieu, "statut": b_statut, "utilisateur": b_user, "debut": b_deb, "fin": b_fin, "suivant": updated_file}
                    
                    # Envoi et attente pour éviter le ghosting Google
                    requests.post(SCRIPT_URL, json=payload)
                    st.success(f"Enregistré pour {f_nom}")
                    time.sleep(1.5)
                    st.rerun()

    if b_file:
        st.write("📋 **Planning :**")
        for i, r in enumerate(b_file.split("|")):
            st.caption(f"{i+1}. {r.strip()}")
    st.divider()
