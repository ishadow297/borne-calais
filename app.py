import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# --- CONFIGURATION ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0LYnrfJWcZqsKjDbTHNzlEhwkiM01eqRCcs-WJDWjXu-V0OhPE7Fv8RIm8hdHIamF/exec"
SHEET_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpyeQVt9fmmpJUEft_YjO52_ivj7gvJxcTTK53R0P3ptPIuKE2-v7pF9TwTJ5PPANlmzMkQwjIinow/pub?output=csv"

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LECTURE ---
try:
    df = pd.read_csv(f"{SHEET_CSV}&nocache={now.microsecond}").fillna("")
    df.columns = df.columns.str.strip()
except:
    st.error("Lien Google Sheets invalide ou non publié.")
    st.stop()

st.title("⚡ Planning des Bornes")

for index, row in df.iterrows():
    statut = str(row['Statut']).lower()
    
    # Gestion des couleurs selon l'état
    bg_color = "#d4edda" # Vert (Libre)
    if "occupe" in statut: bg_color = "#f8d7da" # Rouge
    if "panne" in statut: bg_color = "#fff3cd" # Orange (Panne)

    # --- CARTE DE LA BORNE ---
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{bg_color}; border:1px solid #ccc; margin-bottom:10px">
            <h3 style="margin:0">🔌 {row['Borne']} <small>({row['Lieu']})</small></h3>
            <p style="margin:0"><b>Actuellement :</b> {row['Utilisateur'] if row['Utilisateur'] else 'Libre'}</p>
            <p style="margin:0; font-size:0.9em"><b>Fin prévue :</b> {row['Heure de fin'] if row['Heure de fin'] else '--:--'}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    # --- BOUTON PANNE / RÉPARER ---
    with c1:
        if "panne" in statut:
            if st.button(f"🔧 Remettre en service", key=f"fix_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()
        else:
            if st.button(f"🚩 Signaler Panne", key=f"p_{index}"):
                payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "panne", "utilisateur": "HS", "heure": "", "suivant": row['Suivant']}
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- BOUTON LIBÉRER (Passage au suivant) ---
    with c2:
        if "occupe" in statut:
            if st.button(f"✅ Terminer / Libérer", key=f"lib_{index}"):
                suivants = str(row['Suivant']).split(" | ") if row['Suivant'] else []
                # On nettoie la liste des éléments vides
                suivants = [s for s in suivants if s.strip()]
                
                if suivants:
                    prochain_brut = suivants.pop(0) # On prend le premier
                    # On sépare le nom et l'heure (ex: "Julien (14:00)")
                    try:
                        p_nom = prochain_brut.split(" (")[0]
                        p_heure = prochain_brut.split(" (")[1].replace(")", "")
                    except:
                        p_nom = prochain_brut; p_heure = "En cours"
                        
                    new_suivant = " | ".join(suivants)
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": p_nom, "heure": p_heure, "suivant": new_suivant}
                else:
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "libre", "utilisateur": "", "heure": "", "suivant": ""}
                
                requests.post(SCRIPT_URL, json=payload)
                st.rerun()

    # --- FORMULAIRE DE RÉSERVATION (AJOUT DANS LA LISTE) ---
    with st.expander("📅 Réserver un créneau (aujourd'hui ou plus tard)"):
        nom_res = st.text_input("Ton Prénom", key=f"n_{index}")
        heure_res = st.text_input("Heure de fin (ex: 12:00)", key=f"h_{index}")
        if st.button("Ajouter au planning", key=f"btn_{index}"):
            if nom_res and heure_res:
                if "libre" in statut:
                    # Si personne n'est sur la borne, on l'occupe direct
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": "occupé", "utilisateur": nom_res, "heure": heure_res, "suivant": row['Suivant']}
                else:
                    # Sinon on l'ajoute à la suite dans la colonne 'Suivant'
                    nouveau_creneau = f"{nom_res} ({heure_res})"
                    if row['Suivant']:
                        liste_mise_a_jour = f"{row['Suivant']} | {nouveau_creneau}"
                    else:
                        liste_mise_a_jour = nouveau_creneau
                    
                    payload = {"row": index+1, "borne": row['Borne'], "lieu": row['Lieu'], "statut": row['Statut'], "utilisateur": row['Utilisateur'], "heure": row['Heure de fin'], "suivant": liste_mise_a_jour}
                
                requests.post(SCRIPT_URL, json=payload)
                st.success(f"Planifié pour {nom_res} !")
                st.rerun()

    # Affichage du planning à venir
    if row['Suivant']:
        st.write("🗓 **Prochainement :**")
        for s in str(row['Suivant']).split(" | "):
            st.write(f"• {s}")
    st.divider()
