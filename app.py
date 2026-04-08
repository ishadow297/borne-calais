import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Bornes Gratuites - Calais")

# Connexion
url = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, ttl=0)

st.subheader("État des bornes")

for index, row in df.iterrows():
    col1, col2 = st.columns([1.5, 1])
    status = str(row['Statut']).strip().lower()
    suivant = str(row['Suivant']) if pd.notna(row['Suivant']) else ""

    with col1:
        st.write(f"### {row['Borne']}")
        icon = "🟢" if status == "libre" else "🔴"
        st.write(f"{icon} **{status.upper()}**")
        
        if status != "libre":
            st.write(f"👤 {row['Utilisateur']} | ⏰ Fin : {row['Heure de fin']}")
        
        if suivant != "":
            st.warning(f"⏳ En attente : {suivant}")

    with col2:
        # CAS 1 : LA BORNE EST LIBRE
        if status == "libre":
            nom = st.text_input("Prénom", key=f"n_{index}")
            h = st.text_input("Heure de fin", key=f"h_{index}", placeholder="ex: 15h30")
            if st.button("Réserver", key=f"b_{index}", use_container_width=True):
                if nom and h:
                    df.at[index, 'Statut'] = "Occupé"
                    df.at[index, 'Utilisateur'] = nom
                    df.at[index, 'Heure de fin'] = h
                    conn.update(spreadsheet=url, data=df)
                    st.rerun()

        # CAS 2 : LA BORNE EST OCCUPÉE
        else:
            if suivant == "":
                nom_suiv = st.text_input("Réserver après ?", key=f"s_{index}", placeholder="Ton nom")
                if st.button("Prendre mon tour", key=f"bs_{index}", use_container_width=True):
                    if nom_suiv:
                        df.at[index, 'Suivant'] = nom_suiv
                        conn.update(spreadsheet=url, data=df)
                        st.rerun()
            
            if st.button("Libérer / Fin", key=f"lib_{index}", use_container_width=True):
                if suivant != "":
                    # Si quelqu'un attendait, il prend la place mais doit préciser son heure
                    df.at[index, 'Statut'] = "Occupé"
                    df.at[index, 'Utilisateur'] = suivant
                    df.at[index, 'Heure de fin'] = "À préciser"
                    df.at[index, 'Suivant'] = ""
                else:
                    df.at[index, 'Statut'] = "libre"
                    df.at[index, 'Utilisateur'] = ""
                    df.at[index, 'Heure de fin'] = ""
                conn.update(spreadsheet=url, data=df)
                st.rerun()
    st.divider()
