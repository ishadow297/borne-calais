import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Bornes Gratuites - Calais")

# Connexion au Google Sheets
url = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données (on désactive le cache pour voir les modifs direct)
df = conn.read(spreadsheet=url, ttl=0)

st.subheader("État des bornes en temps réel")

for index, row in df.iterrows():
    col1, col2 = st.columns([1.5, 1])
    
    status = str(row['Statut']).strip().lower()
    icon = "🟢" if status == "libre" else "🔴"
    
    # Préparation du texte d'affichage
    info_user = ""
    if status != "libre":
        user = row['Utilisateur'] if pd.notna(row['Utilisateur']) else "Inconnu"
        heure = row['Heure de fin'] if pd.notna(row['Heure de fin']) else "--h--"
        info_user = f"\n\n👤 {user} | ⏰ Fin : {heure}"

    with col1:
        st.write(f"### {row['Borne']}")
        st.write(f"{icon} **{row['Statut'].upper()}**{info_user}")

    with col2:
        if status == "libre":
            nom = st.text_input("Prénom", key=f"nom_{index}", placeholder="Ton nom")
            heure_saisie = st.text_input("Heure de fin", key=f"h_{index}", placeholder="ex: 14h30")
            
            if st.button("Réserver", key=f"btn_{index}", use_container_width=True):
                if nom and heure_saisie:
                    df.at[index, 'Statut'] = "Occupé"
                    df.at[index, 'Utilisateur'] = nom
                    df.at[index, 'Heure de fin'] = heure_saisie
                    conn.update(spreadsheet=url, data=df)
                    st.success("Réservé !")
                    st.rerun()
                else:
                    st.warning("Remplis le nom et l'heure !")
        else:
            if st.button("Libérer la borne", key=f"lib_{index}", use_container_width=True):
                df.at[index, 'Statut'] = "libre"
                df.at[index, 'Utilisateur'] = ""
                df.at[index, 'Heure de fin'] = ""
                conn.update(spreadsheet=url, data=df)
                st.info("Borne libérée")
                st.rerun()
    st.divider()
