import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

# --- CONNEXION (Mets tes clés ici) ---
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    supabase = create_client(URL, KEY)
except:
    st.error("Lien Supabase mort"); st.stop()

st.set_page_config(page_title="Bornes Calais", layout="centered")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

def piloter(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f or f.strip() in ["", "-"]:
            if b['statut'] != "panne" and b['statut'] != "libre":
                supabase.table("bornes").update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
            continue
        res_list = [r.strip() for r in f.split("|") if r.strip()]
        new_f, user, h_f = [], None, ""
        for r in res_list:
            try:
                nom = r.split(" [")[0]
                t = r.split("[")[1].replace("]","")
                d_s, f_s = t.split(" - ")
                dt_d = datetime.strptime(f"{d_s}/{now.year} %H:%M","%d/%m/%Y %H:%M").replace(tzinfo=tz)
                dt_f = datetime.strptime(f"{f_s}/{now.year} %H:%M","%d/%m/%Y %H:%M").replace(tzinfo=tz)
                if dt_d <= now <= dt_f:
                    user, h_f = nom, f_s
                    new_f.append(r)
                elif dt_d > now: new_f.append(r)
            except: new_f.append(r)
        if b['statut'] != "panne":
            supabase.table("bornes").update({"statut":"occupé" if user else "libre","utilisateur":user if user else "","fin":h_f if h_f else "","suivant":" | ".join(new_f)}).eq("id",bid).execute()

st.title("⚡ Bornes Calais")
st.write(f"🕒 **{now.strftime('%d/%m %H:%M')}**")

try:
    data = supabase.table("bornes").select("*").order("id").execute().data
    piloter(data)
    data = supabase.table("bornes").select("*").order("id").execute().data
except: data = []

for b in data:
    bid, s = str(b['id']), str(b['statut']).lower()
    c = "#ffcccc" if s=="panne" else ("#f8d7da" if s=="occupé" else "#d4edda")
    m = f"🔴 {b['utilisateur']} (fin:{b['fin']})" if s=="occupé" else ("❌ PANNE" if s=="panne" else "🟢 LIBRE")
    st.markdown(f'<div style="padding:15px; border-radius:10px; background:{c}; border:1px solid #555; color:black; margin-bottom:10px"><b>{b["nom"]}</b><br>{m}</div>', unsafe_allow_html=True)
    if st.button("🚩 Panne/OK", key="p"+bid, use_container_width=True):
        ns = "libre"
