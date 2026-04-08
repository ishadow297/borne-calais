import streamlit as st
import pandas as pd
import requests

# Garde bien ton URL Apps Script ici
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfr__TekrEpJGmVEu1SvGqRVIppFOQDQJ_MUp7_lwxSRDZ5NAFVlnoThtybQ7IuZlM/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/export?format=csv"

st.set_page_config(page_title="Planning Bornes", page_icon="⚡")
st.title("⚡ Planning Bornes Calais")

# Lecture des données (on force le rafraîchissement avec un paramètre aléatoire)
df = pd.read_csv(f"{SHEET_CSV}&cache={st.secrets.get('cache_key', 0)}").fillna("")

# --- AFFICHAGE DES BORNES ---
st.header("📍 État et Liste d'attente")

for index, row in df.iterrows():
    status = str(row['Statut']).strip().lower()
    is_libre = status == "libre"
    icon = "🟢" if is_libre else "🔴"
    
    with st.expander(f"{icon} {row['Borne']} - {status.upper()}"):
        col1, col2 = st.columns(2)
        
        with col1:
            if not is_libre:
                st.write(f"👤 **En charge :** {row['Utilisateur']}")
                st.write(f"⏰ **Fin prévue :** {row['Heure de fin']}")
            
            # Affichage de la liste d'attente
            if row['Suivant']:
                st.warning(f"⏳ **Liste d'attente :**\n{row['Suivant']}")
            else:
                st.write("✨ Aucune attente pour cette borne.")

        with col2:
            # Bouton pour libérer la borne complètement
            if st.button(f"Libérer {row['Borne']}", key=f"lib_{index}"):
                payload = {
                    "row": index + 1,
                    "borne": row['Borne'],
                    "statut": "libre",
                    "utilisateur": "",
                    "heure": "",
                    "suivant": row['Suivant'] # On garde la file d'attente même si on libère
                }
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

# --- FORMULAIRE DE RÉSERVATION ---
st.divider()
st.header("📅 Réserver ou s'ajouter à la file")

with st.form("resa_form"):
    borne_nom = st.selectbox("Choisir la borne", df['Borne'].unique())
    type_action = st.radio("Action", ["Prendre la borne (Maintenant)", "S'ajouter à la liste d'attente (Plus tard)"])
    nom = st.text_input("Ton prénom")
    quand = st.text_input("Heure ou Jour (ex: Demain 10h)")
    
    if st.form_submit_button("VALIDER"):
        if nom and quand:
            idx = df[df['Borne'] == borne_nom].index[0]
            current_row = df.iloc[idx]
            
            if type_action == "Prendre la borne (Maintenant)":
                payload = {
                    "row": idx + 1,
                    "borne": borne_nom,
                    "statut": "Occupé",
                    "utilisateur": nom,
                    "heure": quand,
                    "suivant": current_row['Suivant']
                }
            else:
                # On ajoute à la liste d'attente existante
                file_actuelle = str(current_row['Suivant'])
                nouvelle_file = f"{file_actuelle} | {nom}({quand})".strip(" | ")
                payload = {
                    "row": idx + 1,
                    "borne": borne_nom,
                    "statut": current_row['Statut'],
                    "utilisateur": current_row['Utilisateur'],
                    "heure": current_row['Heure de fin'],
                    "suivant": nouvelle_file
                }
            
            requests.post(SCRIPT_URL, json=payload)
            st.success("Planning mis à jour !")
            st.rerun()
