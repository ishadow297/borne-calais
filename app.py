import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Planning des Bornes Calais")

# Connexion au tableur
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données
df = conn.read(ttl=0)

# Nettoyage de sécurité : on transforme tout en texte pour éviter les erreurs AttributeError
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns:
        df[col] = ""
    # On force le format texte et on enlève les erreurs 'nan'
    df[col] = df[col].astype(str).replace('nan', '')

st.header("📍 État des bornes")

# Affichage des bornes
for index, row in df.iterrows():
    status = row['Statut'].strip().lower()
    # Si la case est vide, on considère que c'est libre
    if status not in ['libre', 'occupé']:
        status = 'libre'
        
    with st.expander(f"{row['Borne']} - {'🟢' if status == 'libre' else '🔴'}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Utilisateur :** {row['Utilisateur']}")
            st.write(f"**Fin :** {row['Heure de fin']}")
            if row['Suivant']:
                st.info(f"⏳ Réservé pour : {row['Suivant']}")
        
        with col2:
            if st.button(f"Libérer {row['Borne']}", key=f"lib_{index}"):
                df.at[index, 'Statut'] = "libre"
                df.at[index, 'Utilisateur'] = ""
                df.at[index, 'Heure de fin'] = ""
                conn.update(data=df)
                st.rerun()

# Formulaire de réservation
st.divider()
st.header("📅 Réserver un créneau")

with st.form("resa"):
    borne = st.selectbox("Borne", df['Borne'].unique())
    type_resa = st.radio("Quand ?", ["Maintenant", "Demain / Plus tard"])
    nom = st.text_input("Ton prénom")
    quand = st.text_input("Heure ou Jour (ex: Demain 10h)")
    
    if st.form_submit_button("Enregistrer"):
        if nom and quand:
            idx = df[df['Borne'] == borne].index[0]
            if type_resa == "Maintenant":
                df.at[idx, 'Statut'] = "Occupé"
                df.at[idx, 'Utilisateur'] = nom
                df.at[idx, 'Heure de fin'] = quand
            else:
                # On ajoute à la liste des réservations futures
                actuel = df.at[idx, 'Suivant']
                df.at[idx, 'Suivant'] = f"{actuel} | {nom}({quand})".strip(" | ")
            
            conn.update(data=df)
            st.success("Réservation enregistrée !")
            st.rerun()
