import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz
import time

# --- 1. CONNEXION SUPABASE ---
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

st.set_page_config(page_title="Bornes Calais Auto", layout="centered", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- 2. L'AUTOMATE DE PILOTAGE ---
def piloter_bornes(bornes_data):
    for b in bornes_data:
        file = b.get('suivant') or ""
        if not file or file.strip() == "-" or file.strip() == "":
            # Si vide, on s'assure que la borne est libre (si pas en panne)
            if b['statut'] != "panne" and b['statut'] != "libre":
                supabase.table("bornes").update({"statut": "libre", "utilisateur": "", "fin": ""}).eq("id", b['id']).execute()
            continue
        
        reservations = [r.strip() for r in file.split("|") if r.strip()]
        nouvelle_file = []
        occupe_par = None
        heure_fin_occupe = ""
        
        for res in reservations:
            try:
                # Format : "Nom [JJ/MM HH:MM - JJ/MM HH:MM]"
                nom_client = res.split(" [")[0]
                temps = res.split("[")[1].replace("]", "")
                debut_str, fin_str = temps.split(" - ")
                
                # Conversion en objets datetime
                dt_debut = datetime.strptime(f"{debut_str}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)
                dt_fin = datetime.strptime(f"{fin_str}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)

                if dt_debut <= now <= dt_fin:
                    occupe_par = nom_client
                    heure_fin_occupe = fin_str
                    nouvelle_file.append(res) 
                elif dt_debut > now:
                    nouvelle_file.append(res)
                else:
                    pass # Trop vieux, on supprime (on n'ajoute pas à nouvelle_file)
            except:
                nouvelle_file.append(res) # Garder si format bizarre

        # Mise à jour réelle dans Supabase
        if b['statut'] != "panne":
            statut_final = "occupé" if occupe_par else "libre"
            user_final = occupe_par if occupe_par else ""
            fin_final = heure_fin_occupe if occupe_par else ""
            
            supabase.table("bornes").update({
                "statut": statut_final,
                "utilisateur": user_final,
                "fin": fin_final,
                "suivant": " | ".join(nouvelle_file)
            }).eq("id", b['id']).execute()

# --- 3. AFFICHAGE ---
st.title("⚡ Bornes Calais - Gestion Auto")
st.write(f"🕒 Heure actuelle : **{now.strftime('%d/%m %H:%M')}**")

# Récupération et pilotage
try:
    res = supabase.table("bornes").select("*").order("id").execute()
    bornes = res.data
    piloter_bornes(bornes)
    # Re-lecture pour affichage à jour
    res = supabase.table("bornes").select("*").order("id").execute()
    bornes = res.data
except Exception as e:
    st.error(f"Erreur base de données : {e}")
    bornes = []

for b in bornes:
    statut = str(b['statut']).lower()
    
    # Couleurs
    if statut == "panne":
        color, msg = "#ffcccc", "❌ HORS SERVICE"
    elif statut == "occupé":
        color, msg = "#f8d7da", f"🔴 OCCUPÉ par {b['utilisateur']} (jusqu'à {b['fin']})"
    else:
        color, msg = "#d4edda", "🟢 DISPONIBLE"

    st.markdown(f"""
        <div style="padding:20px; border-radius:15px; background-color:{color}; border:2px solid #555; color:black; margin-bottom:10px">
            <h2 style="margin:0">📍 {b['nom']}</h2>
            <p style="font-size:1.2em; font-weight:bold; margin-top:10px">{msg}</p>
        </div>
    """, unsafe_allow_html=True)

    # Bouton Panne
    label_p = "🔧 Marquer Réparée" if statut == "panne" else "🚩 Signaler Panne"
    if st.button(label_p, key=f"
