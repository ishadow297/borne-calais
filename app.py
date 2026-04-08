import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Planning Bornes Calais", page_icon="⚡")
st.title("⚡ Planning de Recharge")

# Connexion au Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# FORCE TOUTES LES COLONNES EN TEXTE (pour éviter l'erreur TypeError)
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].astype(str).replace('nan', '')

# --- AFFICHAGE ACTUEL ---
st.header("📍 État des bornes")
for index, row in df.iterrows():
    status = str(row['Statut']).strip().lower()
    with st.expander(f"{row['Borne']} - {'🟢 LIBRE' if status == 'libre' else '🔴 OCCUPÉ'}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Actuel :** {row['Utilisateur']}")
            st.write(f"**Fin prévue :** {row['Heure de fin']}")
            if row['Suivant']:
                st.warning(f"⏳ Futur : {row['Suivant']}")
        with col2:
            if st.button(f"Libérer {row['Borne']}", key=f"lib_{index}"):
                df.at[index, 'Statut'] = "libre"
                df.at[index, 'Utilisateur'] = ""
                df.at[index, 'Heure de fin'] = ""
                conn.update(data=df)
                st.rerun()

# --- FORMULAIRE DE RÉSERVATION ---
st.divider()
st.header("📅 Réserver (Aujourd'hui ou +2j)")

with st.form("form_planning"):
    borne_choisie = st.selectbox("Borne", df['Borne'].unique())
    action = st.radio("Quand ?", ["Maintenant (Je me branche)", "Plus tard (Réservation)"])
    nom = st.text_input("Ton prénom")
    quand = st.text_input("Jour / Heure", placeholder="ex: Demain 14h")
    
    if st.form_submit_button("Enregistrer"):
        if nom and quand:
            idx = df[df['Borne'] == borne_choisie].index[0]
            if action == "Maintenant (Je me branche)":
                df.at[idx, 'Statut'] = "Occupé"
                df.at[idx, 'Utilisateur'] = str(nom)
                df.at[idx, 'Heure de fin'] = str(quand)
            else:
                existant = str(df.at[idx, 'Suivant'])
                df.at[idx, 'Suivant'] = f"{existant} | {nom}({quand})".strip(" | ")
            
            conn.update(data=df)
            st.success("Planning mis à jour !")
            st.rerun()
        else:
            st.error("Remplis ton nom et l'heure !")
