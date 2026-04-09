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
        bid = str(b['id'])
        file = b.get('suivant') or ""
        
        if not file or file.strip() in ["", "-"]:
            if b['statut'] != "panne" and b['statut'] != "libre":
                supabase.table("bornes").update({"statut": "libre", "utilisateur": "", "fin": ""}).eq("id", bid).execute()
            continue
        
        reservations = [r.strip() for r in file.split("|") if r.strip()]
        nouvelle_file, occupe_par, heure_fin_occupe = [], None, ""
        
        for res in reservations:
            try:
                nom_client = res.split(" [")[0]
                temps = res.split("[")[1].replace("]", "")
                debut_str, fin_str = temps.split(" - ")
                
                dt_debut = datetime.strptime(f"{debut_str}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)
                dt_fin = datetime.strptime(f"{fin_str}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)

                if dt_debut <= now <= dt_fin:
                    occupe_par = nom_client
                    heure_fin_occupe = fin_str
                    nouvelle_file.append(res) 
                elif dt_debut > now:
                    nouvelle_file.append(res)
            except:
                nouvelle_file.append(res)

        if b['statut'] != "panne":
            s_final = "occupé" if occupe_par else "libre"
            u_final = occupe_par if occupe_par else ""
            f_final = heure_fin_occupe if occupe_par else ""
            
            supabase.table("bornes").update({
