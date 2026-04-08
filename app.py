import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/edit?usp=sharing"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Bornes Gratuites - Calais")

# --- CHARGEMENT DES DONNÉES ---
# Extraction de l'ID du document pour un export propre
sheet_id = "1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error("Impossible de lire le Google Sheets. Vérifie qu'il est bien partagé en 'Tous les utilisateurs disposant du lien'.")
    st.stop()


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

