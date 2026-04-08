import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/edit?usp=sharing"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Bornes Gratuites - Calais")

# --- CHARGEMENT DES DONNÉES ---
# On transforme le lien pour lire le CSV en direct
csv_url = SHEET_URL.replace('/edit#gid=', '/export?format=csv&gid=')
df = pd.read_csv(csv_url)

# --- AFFICHAGE ---
st.subheader("État des bornes en temps réel")

for index, row in df.iterrows():
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.write(f"**{row['Borne']}**")
        status_color = "🟢" if row['Statut'] == "Libre" else "🔴"
        st.write(f"{status_color} {row['Statut']}")

    with col2:
        if row['Statut'] == "Occupé":
            st.write(f"👤 {row['Utilisateur']}")
            st.write(f"⏰ Fin: {row['Heure de fin']}")

    with col3:
        if row['Statut'] == "Libre":
            if st.button(f"Réserver", key=f"btn_{index}"):
                st.info("Pour réserver, envoie un message sur WhatsApp (Lien auto bientôt !)")

