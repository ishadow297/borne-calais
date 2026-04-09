import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

# 1. Connexion
U, K = "https://bbdflpdeehgbgqqqdvnu.supabase.co", "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
T = "bornes"

try:
    db = create_client(U, K)
except:
    st.error("Erreur DB"); st.stop()

# 2. Setup
st.set_page_config(page_title="Bornes")
tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

# 3. Automate
def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] == "occupé" and b['utilisateur'] != "Manuel":
                db.table(T).update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
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
            db.table(T).update({"statut":"occupé" if u else "libre","utilisateur":u or "","fin":hf,"suivant":" | ".join(nf)}).eq("id",bid).execute()

# 4. Interface
st.title("⚡ Bornes Calais")
st.write(f"MAJ: {now.strftime('%H:%M')}")

try:
    d = db.table(T).select("*").order("id").execute().data
    auto(d)
    d = db.table(T).select("*").order("id").execute().data
except: d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    
    # Correction ligne 66 : On utilise des styles Streamlit directs
    if s == "panne":
        st.error(f"📍 {b['nom']} : HORS SERVICE")
    elif s == "occupé":
        st.warning(f"📍 {b['nom']} : {b['utilisateur']} (Fin: {b['fin']})")
    else:
        st.success(f"📍 {b['nom']} : LIBRE")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚩 Panne/OK", key="p"+bid):
            ns = "libre" if s == "panne" else "panne"
            db.table
