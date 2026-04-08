import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
st.title("⚡ Planning des Bornes Calais")

# Connexion stable
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture forcée (ttl=0 pour voir les changements en direct)
df = conn.read(ttl=0)

# PROTECTION : On transforme tout en texte pour éviter les crashs (AttributeError)
for col in ['Statut', 'Utilisateur', 'Heure de fin', 'Suivant']:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].astype(str).replace('nan', '').replace('None', '')

st.header("📍 État des bornes")

# Affichage des bornes sous forme de menus déroulants
for index, row in df.iterrows():
    status = row['Statut'].strip().lower()
    # Sécurité si la case est mal remplie
    if status not in ['libre', 'occupé']:
        status = 'libre'
        
    with st.expander(f"{row['Borne']} - {'🟢' if status == 'libre' else '🔴'}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Actuel :** {row['Utilisateur']}")
            st.write(f"**Fin :** {row['Heure de fin']}")
            if row['Suivant']:
                st.warning(f"⏳ Réservé : {row['Suivant']}")
        
        with col2:
            if st.button(f"Libérer {row['Borne']}", key=f"lib_{index}"):
                df.at[index, 'Statut'] = "libre"
                df.at[index, 'Utilisateur'] = ""
                df.at[index, 'Heure de fin'] = ""
                conn.update(data=df)
                st.rerun()

# FORMULAIRE POUR RÉSERVER (Aujourd'hui, Demain, etc.)
st.divider()
st.header("📅 Réserver un créneau")

with st.form("form_planning"):
    borne_choisie = st.selectbox("Choisir la borne", df['Borne'].unique())
    moment = st.radio("Quand ?", ["Je me branche MAINTENANT", "Je réserve pour PLUS TARD / DEMAIN"])
    nom = st.text_input("Ton prénom")
    h_fin = st.text_input("Jour et Heure", placeholder="ex: Demain 14h / Mardi matin")
    
    if st.form_submit_button("ENREGISTRER"):
        if nom and h_fin:
            idx = df[df['Borne'] == borne_choisie].index[0]
            if moment == "Je me branche MAINTENANT":
                df.at[idx, 'Statut'] = "Occupé"
                df.at[idx, 'Utilisateur'] = nom
                df.at[idx, 'Heure de fin'] = h_fin
            else:
                # On ajoute la réservation à la suite dans la colonne "Suivant"
                actuel = df.at[idx, 'Suivant']
                nouveau = f"[{nom}: {h_fin}]"
                df.at[idx, 'Suivant'] = f"{actuel} {nouveau}".strip()
            
            conn.update(data=df)
            st.success("C'est enregistré dans le planning !")
            st.rerun()
        else:
            st.error("Merci de remplir ton nom et l'heure.")
