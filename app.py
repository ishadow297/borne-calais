import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

# --- CONFIG ---
U, K = "https://bbdflpdeehgbgqqqdvnu.supabase.co", "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
T = "bornes"

try:
    db = create_client(U, K)
except:
    st.error("DB Error"); st.stop()

st.set_page_config(page_title="Bornes Calais")
tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

# Traduction manuelle des jours
jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
nom_jour = jours[now.weekday()]
mois = ["Jan.", "Fév.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]
nom_mois = mois[now.month - 1]

def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] not in ["panne", "libre"] and b['utilisateur'] != "Manuel":
                db.table(T).update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
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
            db.table(T).update({"statut":"occupé" if u else "libre","utilisateur":u or "","fin":hf,"suivant":" | ".join(nf)}).eq("id",bid).execute()

st.title("⚡ Bornes Calais")
st.info(f"📅 **{nom_jour} {now.day} {nom_mois}** | 🕒 **{now.strftime('%H:%M')}**")

try:
    d = db.table(T).select("*").order("id").execute().data
    auto(d)
    d = db.table(T).select("*").order("id").execute().data
except: d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    with st.container():
        st.subheader(f"📍 {b['nom']}")
