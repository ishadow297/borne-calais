import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Planning Bornes Calais", page_icon="⚡")
st.title("⚡ Planning de Recharge")

# Connexion au Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# On s'assure que toutes les colonnes nécessaires existent
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns:
        df[col] = ""

# --- AFFICHAGE ACTUEL ---
st.header("📍 État des bornes en direct")
for index, row in df.iterrows():
    status = str(row['Statut']).strip().lower()
    with st.expander(f"{row['Borne']} - {'🟢 LIBRE' if status == 'libre' else '🔴 OCCUPÉ'}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Utilisateur actuel :** {row['Utilisateur']}")
            st.write(f"**Fin prévue :** {row['Heure de fin']}")
            if row['Suivant']:
                st.warning(f"⏳ Réservations futures : {row['Suivant']}")
        with col2:
            if st.button(f"Libérer la borne {row['Borne']}", key=f"lib_{index}"):
                df.at[index, 'Statut'] = "libre"
                df.at[index, 'Utilisateur'] = ""
                df.at[index, 'Heure de fin'] = ""
                # On peut choisir de garder ou non les réservations futures ici
                conn.update(data=df)
                st.rerun()

# --- FORMULAIRE DE RÉSERVATION ---
st.divider()
st.header("📅 Réserver un créneau (Aujourd'hui, Demain, +2j)")

with st.form("form_planning"):
    borne_choisie = st.selectbox("Choisir la borne", df['Borne'].unique())
    action = st.radio("Moment de la recharge", ["Je me branche MAINTENANT", "Je réserve pour PLUS TARD / DEMAIN"])
    nom = st.text_input("Votre prénom")
    quand = st.text_input("Jour et Heure", placeholder="ex: Demain 14h / Mardi matin")
    
    valider = st.form_submit_button("Enregistrer ma réservation")
    
    if valider:
        if nom and quand:
            idx = df[df['Borne'] == borne_choisie].index[0]
            if action == "Je me branche MAINTENANT":
                df.at[idx, 'Statut'] = "Occupé"
                df.at[idx, 'Utilisateur'] = nom
                df.at[idx, 'Heure de fin'] = quand
            else:
                # On ajoute la nouvelle réservation à la liste existante
                planning_existant = str(df.at[idx, 'Suivant']) if pd.notna(df.at[idx, 'Suivant']) else ""
                nouvelle_resa = f"[{nom} : {quand}]"
                df.at[idx, 'Suivant'] = f"{planning_existant} {nouvelle_resa}".strip()
            
            conn.update(data=df)
            st.success(f"Réservation enregistrée pour {nom} !")
            st.rerun()
        else:
            st.error("Merci de remplir votre nom et le créneau souhaité.")
