import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais Pro", page_icon="⚡", layout="centered")

# --- STYLE CSS POUR LES COULEURS ---
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd; }
    .libre { background-color: #d4edda; border-left: 10px solid #28a745; }
    .occupe { background-color: #f8d7da; border-left: 10px solid #dc3545; }
    .panne { background-color: #fff3cd; border-left: 10px solid #ffc107; }
    </style>
    """, unsafe_allow_html=True)

# --- TEMPS ---
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)
date_j = now.strftime("%d/%m")
heure_j = now.strftime("%H:%M")

df = pd.read_csv(f"{SHEET_CSV}&cache={now.second}").fillna("")

st.title("⚡ Bornes de Recharge Calais")
st.info(f"📅 Nous sommes le **{date_j}** | 🕒 Il est **{heure_j}**")

# --- AFFICHAGE DES BORNES ---
for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    
    # Détermination de la classe CSS et de l'icône
    css_class = "libre"
    icon = "✅"
    if statut == "occupé":
        css_class = "occupe"
        icon = "🚗"
    elif statut == "panne":
        css_class = "panne"
        icon = "⚠️"

    # Calcul de la barre de progression (si occupé)
    progress = 0
    if statut == "occupé" and " | " in str(row['Heure de fin']):
        try:
            times = str(row['Heure de fin']).split(" | ")[1].split(" >> ")
            start_t = datetime.strptime(times[0], "%H:%M")
            end_t = datetime.strptime(times[1], "%H:%M")
            now_t = datetime.strptime(heure_j, "%H:%M")
            total = (end_t - start_t).total_seconds()
            ecoule = (now_t - start_t).total_seconds()
            progress = min(max(ecoule / total, 0.0), 1.0) if total > 0 else 0
        except: pass

    # Affichage de la "Carte"
    st.markdown(f"""<div class="status-card {css_class}">
        <h3>{icon} {row['Borne']}</h3>
        <p><b>Statut :</b> {statut.capitalize()}</p>
    </div>""", unsafe_allow_html=True)

    if statut == "occupé":
        st.write(f"👤 **{row['Utilisateur']}** jusqu'à **{row['Heure de fin'].split(' >> ')[1]}**")
        st.progress(progress)
    
    if row['Suivant']:
        with st.expander("📅 Voir la file d'attente"):
            st.write(row['Suivant'].replace(" | ", "\n\n"))

    # Boutons d'action rapides
    c1, c2 = st.columns(2)
    with c1:
        if statut != "panne" and st.button(f"🚩 Signaler Panne ({row['Borne']})", key=f"p_{index}"):
            requests.post(SCRIPT_URL, json={"row": index+1, "borne": row['Borne'], "statut": "panne", "utilisateur": "S.O.S", "heure": "", "suivant": row['Suivant']})
            st.rerun()
    with c2:
        if statut != "libre" and st.button(f"🔄 Libérer ({row['Borne']})", key=f"l_{index}"):
            requests.post(SCRIPT_URL, json={"row": index+1, "borne": row['Borne'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": row['Suivant']})
            st.rerun()

# --- FORMULAIRE ---
st.divider()
st.subheader("📅 Nouvelle Réservation")
with st.form("resa"):
    b = st.selectbox("Borne", df['Borne'].unique())
    j = st.radio("Jour", [f"Aujourd'hui ({date_j})", f"Demain"])
    n = st.text_input("Prénom")
    h_list = [f"{h:02d}:{m:02d}" for h in range(7, 22) for m in (0, 30)]
    c3, c4 = st.columns(2)
    h_s = c3.selectbox("Début", h_list, index=4)
    h_e = c4.selectbox("Fin", h_list, index=8)
    
    if st.form_submit_button("VALIDER"):
        if n and h_s < h_e:
            idx = df[df['Borne'] == b].index[0]
            jour_txt = date_j if "Aujourd'hui" in j else (now + pd.Timedelta(days=1)).strftime("%d/%m")
            txt_final = f"{jour_txt} | {h_s} >> {h_e}"
            
            # Si libre, on occupe, sinon on ajoute à 'Suivant'
            if str(df.iloc[idx]['Statut']).lower() == "libre":
                payload = {"row": idx+1, "borne": b, "statut": "Occupé", "utilisateur": n, "heure": txt_final, "suivant": df.iloc[idx]['Suivant']}
            else:
                new_f = f"{df.iloc[idx]['Suivant']} | • {n} ({txt_final})".strip(" | ")
                payload = {"row": idx+1, "borne": b, "statut": df.iloc[idx]['Statut'], "utilisateur": df.iloc[idx]['Utilisateur'], "heure": df.iloc[idx]['Heure de fin'], "suivant": new_f}
            
            requests.post(SCRIPT_URL, json=payload)
            st.success("C'est enregistré !")
            st.rerun()
