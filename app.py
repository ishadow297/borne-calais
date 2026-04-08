import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Bornes Gratuites - Calais")

# Connexion sécurisée
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0) # ttl=0 pour forcer la mise à jour
except Exception as e:
    st.error("Erreur de connexion au Google Sheets. Vérifie les 'Secrets' sur Streamlit.")
    st.stop()

# Sécurité colonnes
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns:
        df[col] = ""

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
            st.write(f"👤 {row['Utilisateur']} | ⏰ Fin : {row['Heure de fin']}")
        if suivant != "":
            st.warning(f"⏳ Prochain : {suivant}")

    with col2:
        if status == "libre":
            nom = st.text_input("Prénom", key=f"n_{index}")
            h = st.text_input("Fin", key=f"h_{index}", placeholder="ex: 15h30")
            if st.button("Réserver", key=f"b_{index}"):
                if nom and h:
                    df.at[index, 'Statut'] = "Occupé"
                    df.at[index, 'Utilisateur'] = nom
                    df.at[index, 'Heure de fin'] = h
                    conn.update(data=df)
                    st.rerun()
        else:
            if suivant == "":
                nom_suiv = st.text_input("Après ?", key=f"s_{index}")
                if st.button("Prendre mon tour", key=f"bs_{index}"):
                    if nom_suiv:
                        df.at[index, 'Suivant'] = nom_suiv
                        conn.update(data=df)
                        st.rerun()
            
            if st.button("Libérer", key=f"lib_{index}"):
                if suivant != "":
                    df.at[index, 'Statut'] = "Occupé"; df.at[index, 'Utilisateur'] = suivant; df.at[index, 'Heure de fin'] = "À préciser"; df.at[index, 'Suivant'] = ""
                else:
                    df.at[index, 'Statut'] = "libre"; df.at[index, 'Utilisateur'] = ""; df.at[index, 'Heure de fin'] = ""; df.at[index, 'Suivant'] = ""
                conn.update(data=df)
                st.rerun()
    st.divider()
