import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

# --- CONFIG ---
U = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
K = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    db = create_client(U, K)
except:
    st.error("Erreur"); st.stop()

st.set_page_config(page_title="Bornes Calais", layout="centered")

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    .borne-card {
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 10px solid;
    }
    .statut-label {
        font-weight: bold;
        font-size: 1.2em;
        text-transform: uppercase;
    }
    .user-info {
        font-size: 1.1em;
        color: #333;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

# --- AUTOMATE ---
def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] not in ["panne", "libre"] and b['utilisateur'] != "Manuel":
                db.table("bornes").update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
            continue
        rl, nf, u, hf = [r.strip() for r in f.split("|") if r.strip()], [], None, ""
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

# --- HEADER ---
st.title("⚡ Bornes Calais Auto")
st.subheader(f"🕒 {now.strftime('%H:%M')}")

try:
    res = db.table("bornes").select("*").order("id").execute()
    d = res.data
    auto(d)
    d = db.table("bornes").select("*").order("id").execute().data
except: d = []

# --- AFFICHAGE ---
for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    
    # Choix du style selon le statut
    if s == "panne":
        bg, border, txt = "#ffebee", "#f44336", "HORS SERVICE"
    elif s == "occupé":
        bg, border, txt = "#fff3e0", "#ff9800", f"OCCUPÉ - {b['utilisateur']}"
    else:
        bg, border, txt = "#e8f5e9", "#4caf50", "DISPONIBLE"

    st.markdown(f"""
    <div class="borne-card" style="background-color: {bg}; border-left-color: {border};">
        <div style
