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
    st.error("Erreur connexion"); st.stop()

st.set_page_config(page_title="Bornes Calais", layout="centered")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

def piloter(data):
    for b in data:
        bid = str(b['id'])
        file = b.get('suivant') or ""
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
                dt_d = datetime.strptime(f"{d_s}/{now.year}","%d/%m %H:%M/%Y").replace(tzinfo=tz)
                dt_f = datetime.strptime(f"{f_s}/{now.year}","%d/%m %H:%M/%Y").replace(tzinfo=tz)
                # Si le créneau est en cours
                if dt_d <= now <= dt_f:
                    user, h_f = nom, f_s
                    new_f.append(r)
                elif dt_d > now: new_f.append(r)
            except: new_f.append(r)
        
        if b['statut']
