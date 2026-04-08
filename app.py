import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Bornes Gratuites - Calais")

# Connexion
url = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture forcée sans mémoire cache
df = conn.read(spreadsheet=url, ttl=0)

# Sécurité : Si la colonne Suivant n'est pas encore détectée, on l'ajoute virtuellement
if 'Suivant' not in df.columns:
    df['Suivant'] = ""

st.subheader("État des bornes")

for index, row in df.iterrows():
    col1, col2 = st.columns([1.5, 1])
    status = str(row['Statut']).strip().lower()
    suivant = str(row['Suivant']) if pd.notna(row['Suivant']) and str(row['Suivant']) != "nan" else ""

    with col1:
        st.write(f"### {row['Borne']}")
        icon = "🟢" if status == "libre" else "🔴"
        st.write(f"{icon} **{status.upper()}**")
        
        if status != "libre":
            u = row['Utilisateur'] if pd.notna(row['Utilisateur']) else "Inconnu"
            h = row['Heure de fin'] if pd.notna(row['Heure de fin']) else "--h--"
            st.write(f"👤 {u} | ⏰ Fin : {h}")
        
        if suivant != "":
            st.warning(f"⏳ Prochain : {suivant}")

    with col2:
        if status == "libre":
            nom = st.text_input("Prénom", key=f"n_{index}")
            h_fin = st.text_input("Heure de fin", key=f"h_{index}", placeholder="ex: 15h30")
            if st.button("Réserver", key=f"b_{index}", use_container_width=True):
                if nom and h_fin:
                    df.at[index, 'Statut'] = "Occupé"
                    df.at[index, 'Utilisateur'] = nom
                    df.at[index, 'Heure de fin'] = h_fin
                    conn.update(spreadsheet=url, data=df)
                    st.rerun()
        else:
            if suivant == "":
                nom_suiv = st.text_input("Réserver après ?", key=f"s_{index}")
                if st.button("Prendre mon tour", key=f"bs_{index}", use_container_width=True):
                    if nom_suiv:
                        df.at[index, 'Suivant'] = nom_suiv
                        conn.update(spreadsheet=url, data=df)
                        st.rerun()
            
            if st.button("Libérer", key=f"lib_{index}", use_container_width=True):
                if suivant != "":
                    df.at[index, 'Statut'] = "Occupé"
                    df.at[index, 'Utilisateur'] = suivant
                    df.at[index, 'Heure de fin'] = "À préciser"
                    df.at[index, 'Suivant'] = ""
                else:
                    df.at[index, 'Statut'] = "libre"
                    df.at[index, 'Utilisateur'] = ""
                    df.at[index, 'Heure de fin'] = ""
                    df.at[index, 'Suivant'] = ""
                conn.update(spreadsheet=url, data=df)
                st.rerun()
    st.divider()
