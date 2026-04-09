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

st.title("⚡ Bornes Calais")

try:
    res = db.table("bornes").select("*").order("id").execute()
    d = res.data
    auto(d)
    d = db.table("bornes").select("*").order("id").execute().data
except: d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    
    with st.container():
        st.subheader(f"📍 {b['nom']}")
        if s == "panne": st.error("❌ HORS SERVICE")
        elif s == "occupé": st.warning(f"🔴 OCCUPÉ par {b['utilisateur']} (Fin: {b['fin']})")
        else: st.success("🟢 DISPONIBLE")

        c1, c2 = st.columns(2)
        if st.button("🚩 Panne/OK", key="p"+bid, use_container_width=True):
            ns = "libre" if s == "panne" else "panne"
            db.table("bornes").update({"statut":ns,"utilisateur":"","fin":""}).eq("id",bid).execute()
            st.rerun()
        
        if s == "libre":
            if st.button("🚗 Occuper", key="o"+bid, use_container_width=True):
                db.table("bornes").update({"statut":"occupé","utilisateur":"Manuel","fin":"--"}).eq("id",bid).execute()
                st.rerun()
        else:
            if st.button("✅ Libérer", key="l"+bid, use_container_width=True):
                db.table("bornes").update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
                st.rerun()

    with st.expander("📅 Réserver (Vérification auto)"):
        with st.form(key="f"+bid, clear_on_submit=True):
            n = st.text_input("Prénom")
            h1 = st.selectbox("Début", [f"{h:02d}:00" for h in range(24)], index=now.hour)
            h2 = st.selectbox("Fin", [f"{h:02d}:00" for h in range(24)], index=(now.hour+1)%24)
            
            if st.form_submit_button("VALIDER"):
                if n and h1 < h2:
                    debut_test = datetime.strptime(f"{now.strftime('%d/%m')}/{now.year} {h1}", fmt).replace(tzinfo=tz)
                    fin_test = datetime.strptime(f"{now.strftime('%d/%m')}/{now.year} {h2}", fmt).replace(tzinfo=tz)
                    conflit = False
                    
                    # Vérification des créneaux existants
                    if b['suivant'] and b['suivant'] != "-":
                        for r in b['suivant'].split("|"):
                            try:
                                t = r.split("[")[1].replace("]","")
                                ds, fs = t.split(" - ")
                                dd = datetime.strptime(f"{ds}/{now.year}", fmt).replace(tzinfo=tz)
                                df = datetime.strptime(f"{fs}/{now.year}", fmt).replace(tzinfo=tz)
                                # Logique de collision : (Début1 < Fin2) AND (Fin1 > Début2)
                                if debut_test < df and fin_test > dd:
                                    conflit = True
                                    break
                            except: continue
                    
                    if conflit:
                        st.error("⚠️ Ce créneau est déjà réservé !")
                    else:
                        tr = f"{n} [{now.strftime('%d/%m')} {h1} - {now.strftime('%d/%m')} {h2}]"
                        old = b['suivant'] or ""
                        maj = f"{old} | {tr}" if (old and old!="-") else tr
                        db.table("bornes").update({"suivant":maj}).eq("id",bid).execute()
                        st.success("Réservé !")
                        time.sleep(1)
                        st.rerun()
                elif h1 >= h2:
                    st.error("L'heure de fin doit être après l'heure de début.")

    if b['suivant'] and b['suivant'].strip() not in ["", "-"]:
        for i in b['suivant'].split("|"):
            if i.strip(): st.caption(f"• {i.strip()}")
    st.divider()

time.sleep(60)
st.rerun()
