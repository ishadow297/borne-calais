import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import time

# --- 1. CONNEXION SUPABASE ---
# Remplace avec tes propres clés (Dashboard Supabase > Settings > API)
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# Configuration de la page
st.set_page_config(page_title="Bornes Calais Auto", layout="centered", page_icon="⚡")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- 2. L'AUTOMATE DE PILOTAGE ---
def piloter_bornes(bornes_data):
    for b in bornes_data:
        file = b.get('suivant') or ""
        # On ignore si la file est vide ou contient juste un tiret
        if not file or file.strip() == "-":
            if b['statut'] != "panne" and (b['utilisateur'] != "" or b['statut'] != "libre"):
                supabase.table("bornes").update({"statut": "libre", "utilisateur": "", "fin": ""}).eq("id", b['id']).execute()
            continue
        
        reservations = [r.strip() for r in file.split("|") if r.strip()]
        nouvelle_file = []
        occupe_par = None
        heure_fin_occupe = ""
        a_change = False
        
        for res in reservations:
            try:
                # Format attendu : "Nom [JJ/MM HH:MM - JJ/MM HH:MM]"
                nom_client = res.split(" [")[0]
                temps = res.split("[")[1].replace("]", "")
                debut_str, fin_str = temps.split(" - ")
                
                # Conversion en objets datetime pour comparaison réelle
                dt_debut = datetime.strptime(f"{debut_str}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)
                dt_fin = datetime.strptime(f"{fin_str}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)

                # CAS 1 : Le créneau est EN COURS
                if dt_debut <= now <= dt_fin:
                    occupe_par = nom_client
                    heure_fin_
