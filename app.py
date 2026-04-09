import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

# --- CONFIG ---
U, K = "https://bbdflpdeehgbgqqqdvnu.supabase.co", "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    db = create_client(U, K)
except:
    st.error("Erreur DB"); st.stop()

st.set_page_config(page_title="Bornes Calais", layout="centered")
tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] not in ["panne", "libre"] and b['utilisateur'] != "Manuel":
                db.table("bornes").update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
            continue
        rl = [r.strip() for r in f.split("|") if r.strip()]
        nf, u, hf = [], None, ""
        for r in rl:
            try:
                nm = r.split(" [")[0]
                t = r.split("[")[1].replace("]","")
                ds, fs = t.split(" - ")
                dd = datetime.strptime(f"{ds}/{now.year}", fmt).replace(tzinfo=tz)
                df = datetime.strptime(f"{fs}/{now.year}", fmt).replace(tzinfo=tz)
                if dd <= now <= df:
                    u, hf = nm, fs.split(" ")[1]
                    nf.append(r)
                elif dd > now: nf.append(r)
            except: nf.append(r)
        if b['statut'] != "panne" and b['utilisateur'] != "Manuel":
            db.table("bornes").update({"statut":"occupé" if u else "libre","utilisateur":u or "","fin":hf,"suivant":" | ".join(nf)}).eq("id",bid).execute()

# --- HEADER AVEC DATE ET HEURE ---
st.title("⚡ Bornes Calais")
# Affichage de la date : "Jeudi 09 Avril - 23:30"
st.info(f"📅 **{now.strftime('%A %d %b')}** | 🕒 **{now.strftime('%H:%M')}**")

try:
    res = db.table("bornes").select("*").order("id").execute()
    d = res.data
    auto(d)
    d = db.table("born
