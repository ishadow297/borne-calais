import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pytz, time

# --- CONFIGURATION ---
# Remplace par tes vrais identifiants si besoin
U = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
K = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
T = "bornes"

try:
    db = create_client(U, K)
except:
    st.error("Connexion à la base de données impossible")
    st.stop()

# --- RÉGLAGES TEMPORELS ---
st.set_page_config(page_title="Bornes Calais", layout="centered")
tz = pytz.timezone('Europe/Paris')
fmt = "%d/%m/%Y %H:%M"
now = datetime.now(tz)

# Traduction française manuelle pour l'en-tête
js = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
ms = ["Janv.","Févr.","Mars","Avril","Mai","Juin","Juil.","Août","Sept.","Oct.","Nov.","Déc."]
d_fr = f"{js[now.weekday()]} {now.day} {ms[now.month-1]}"

# --- AUTOMATE DE GESTION ---
def auto(data):
    for b in data:
        bid = str(b['id'])
        f = b.get('suivant') or ""
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
                # On utilise l'année dynamique pour le parsing
                dd = datetime.strptime(f"{ds}/{now.year}", fmt).replace(tzinfo=tz)
                df = datetime.strptime(f"{fs}/{now.year}", fmt).replace(tzinfo=tz)
                
                if dd <= now <= df:
                    u, hf = nm, fs.split(" ")[1]
                    nf.append(r)
                elif dd > now:
                    nf.append(r)
            except:
                nf.append(r)
        
        if b['statut'] != "panne" and b['utilisateur'] != "Manuel":
            db.table(T).update({
                "statut": "occupé" if u else "libre",
                "utilisateur": u or "",
                "fin": hf,
                "suivant": " | ".join(nf)
            }).eq("id", bid).execute()

# --- INTERFACE PRINCIPALE ---
st.title("⚡ Bornes Calais")
st.info(f"📅 **{d_fr}** | 🕒 **{now.strftime('%H:%M')}**")

try:
    res = db.table(T).select("*").order("id").execute()
    d = res.data
    auto(d) 
    d = db.table(T).select("*").order("id").execute().data
except:
    d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    
    with st.container():
        st.subheader(f"📍 {b['nom']}")
        
        if s == "panne":
            st.error("❌ HORS SERVICE")
        elif s == "occupé":
            st.warning(f"🔴 OCCUPÉ par {b['utilisateur']} (Jusqu'à: {b['fin']})")
        else:
