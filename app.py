import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Bornes Gratuites - Calais")

# --- CONFIGURATION ---
SHEET_ID = "1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Lecture des données
try:
    df = pd.read_csv(SHEET_URL)
except:
    st.error("Problème de lecture du tableau.")
    st.stop()

# Sécurité colonnes
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns:
        df[col] = ""

st.subheader("État des bornes")

for index, row in df.iterrows():
    col1, col2 = st.columns([1.5, 1])
    status = str(row['Statut']).strip().lower()
    borne = row['Borne']
    
    with col1:
        icon = "🟢" if status == "libre" else "🔴"
        st.write(f"### {borne}")
        st.write(f"{icon} **{status.upper()}**")
        if status != "libre":
            st.write(f"👤 {row['Utilisateur']} | ⏰ Fin : {row['Heure de fin']}")
        if pd.notna(row['Suivant']) and str(row['Suivant']) != "" and str(row['Suivant']) != "nan":
            st.warning(f"⏳ Prochain : {row['Suivant']}")

    with col2:
        # Pour simplifier et éviter les erreurs de droits, on utilise un bouton WhatsApp
        # qui pré-remplit le message pour toi
        msg = f"Je réserve la borne {borne}"
        link = f"https://wa.me/336XXXXXXXX?text={urllib.parse.quote(msg)}" # Remplace par ton numéro
        
        if status == "libre":
            st.link_button("🚀 Réserver (WhatsApp)", link, use_container_width=True)
        else:
            st.link_button("⏳ Prendre mon tour", link, use_container_width=True)
    st.divider()

st.info("Note : Pour mettre à jour le statut, changez-le directement dans le Google Sheets partagé.")
