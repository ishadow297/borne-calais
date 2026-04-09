import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

# --- CONNEXION ---
U, K = "https://bbdflpdeehgbgqqqdvnu.supabase.co", "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    db = create_client(U, K)
except:
    st.error("Lien mort"); st.stop()

# --- CONFIG & AUTO-REFRESH (Toutes les 60 secondes) ---
st.set_page_config(page_title="Bornes Calais", layout="centered")
# Cette ligne force l'appli à se mettre à jour toute seule
st.empty() 

tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        # 1. Nettoyage si file vide
        if not f.strip() or f.strip() == "-":
            if b['statut'] != "panne" and b['statut'] != "libre" and b['utilisateur'] != "Manuel":
                db.table("bornes").update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
            continue
        
        # 2. Analyse de la file
        rl = [r.strip() for r in f.split("|") if r.strip()]
        nf, u, hf = [], None, ""
        
        # Supprimer les doublons exacts dans la file
        rl = list(dict.fromkeys(rl)) 
        
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
                elif dd > now: 
                    nf.append(r)
            except: 
                nf.append(r)

        # 3. Mise à jour auto (sauf si forcé en Manuel)
        if b['statut'] != "panne" and b['utilisateur'] != "Manuel":
            db.table("bornes").update({
                "statut":"occupé" if u else "libre",
                "utilisateur":u or "",
                "fin":hf,
                "suivant":" | ".join(nf)
            }).eq("id",bid).execute()

# --- INTERFACE ---
st.title("⚡ Bornes Calais Pro")
st.info(f"🕒 Heure système : **{now.strftime('%H:%M')}** (Actualisé auto)")

try:
    d = db.table("bornes").select("*").order("id").execute().data
    auto(d)
    d = db.table("bornes").select("*").order("id").execute().data
except: d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    c = "#ffcccc" if s=="panne" else ("#f8d7da" if s=="occupé" else "#d4edda")
    
    # Texte du statut
    if s == "occupé":
        m = f"🔴 **OCCUPÉ** par **{b['utilisateur']}**"
        if b['fin']: m += f" (fin prévue : {b['fin']})"
    elif s == "panne":
        m = "❌ **HORS SERVICE**"
    else:
        m = "🟢 **DISPONIBLE**"

    st.markdown(f'''
        <div style="padding:20px; border-radius:15px; background:{c}; color:black; border:2px solid #444; margin-bottom:10px">
            <h2 style="margin:0; font-size:25px;">{b["nom"]}</h2>
            <div style="font-size:18px; margin-top:10px;">{m}</div>
        </div>
    ''', unsafe_allow_html=True)

    # Boutons d'action rapides
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚩 Panne/OK", key="p"+bid, use_container_width=True):
            ns = "libre" if s=="panne" else "panne"
            db.table("bornes").update({"statut":ns,"utilisateur":"","fin":""}).eq("id",bid).execute()
            st.rerun()
    with col2:
        if s == "libre":
            if st.button("🚗 Forcer Occupé", key="o"+bid, use_container_width=True):
                db.table("bornes").update({"statut":"occupé","utilisateur":"Manuel","
