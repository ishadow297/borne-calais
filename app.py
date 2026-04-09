import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

# 1. Connexion (Vérifie bien tes clés ici)
U = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
K = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
T = "bornes"

try:
    db = create_client(U, K)
except:
    st.error("Lien base de données mort")
    st.stop()

# 2. Configuration
st.set_page_config(page_title="Bornes Calais")
tz = pytz.timezone('Europe/Paris')
fmt = "%d/%m/%Y %H:%M"
now = datetime.now(tz)

# 3. Fonction Automate
def auto(data):
    for b in data:
        bid = str(b['id'])
        f = b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] != "panne" and b['statut'] != "libre" and b['utilisateur'] != "Manuel":
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

# 4. Interface
st.title("⚡ Bornes Calais")
st.write(f"Heure : {now.strftime('%d/%m %H:%M')}")

try:
    res = db.table(T).select("*").order("id").execute()
    d = res.data
    auto(d)
    d = db.table(T).select("*").order("id").execute().data
except Exception as e:
    st.error(f"Erreur de lecture : {e}")
    d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    
    # Couleur de la boîte
    c =
