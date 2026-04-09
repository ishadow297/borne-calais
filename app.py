import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pytz, time

# --- CONNEXION ---
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    supabase = create_client(URL, KEY)
except:
    st.error("Lien Supabase mort"); st.stop()

st.set_page_config(page_title="Bornes Calais", layout="centered")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- AUTOMATE ---
def piloter(data):
    for b in data:
        bid = str(b['id'])
        file = b.get('suivant') or ""
        
        # Si rien dans le planning, on libère la borne (si pas en panne)
        if not file or file.strip() in ["", "-"]:
            if b['statut'] != "panne" and b['statut'] != "libre":
                supabase.table("bornes").update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
            continue
        
        res_list = [r.strip() for r in file.split("|") if r.strip()]
        new_f, user, h_f = [], None, ""
        
        for r in res_list:
            try:
                nom = r.split(" [")[0]
                t = r.split("[")[1].replace("]","")
                d_s, f_s = t.split(" - ")
                # Format: JJ/MM HH:MM
                dt_d = datetime.strptime(f"{d_s}/{now.year}","%d/%m/%Y %H:%M").replace(tzinfo=tz)
                dt_f = datetime.strptime(f"{f_s}/{now.year}","%
