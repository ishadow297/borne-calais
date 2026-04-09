import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz, time

U, K = "https://bbdflpdeehgbgqqqdvnu.supabase.co", "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    db = create_client(U, K)
except:
    st.error("Lien mort"); st.stop()

st.set_page_config(page_title="Bornes", layout="centered")
tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] != "panne" and b['statut'] != "libre":
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
        if b['statut'] != "panne":
            db.table("bornes").update({"statut":"occupé" if u else "libre","utilisateur":u or "","fin":hf,"suivant":" | ".join(nf)}).eq("id",bid).execute()

st.title("⚡ Bornes Calais")
try:
    d = db.table("bornes").select("*").order("id").execute().data
    auto(d)
    d = db.table("bornes").select("*").order("id").execute().data
except: d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    c = "#ffcccc" if s=="panne" else ("#f8d7da" if s=="occupé" else "#d4edda")
    m = f"🔴 {b['utilisateur']} (fin:{b['fin']})" if s=="occupé" else ("❌ PANNE" if s=="panne" else "🟢 LIBRE")
    st.markdown(f'<div style="padding:15px;border-radius:10px;background:{c};color:black;margin-bottom:10px"><b>{b["nom"]}</b><br>{m}</div>', unsafe_allow_html=True)

    if st.button("🚩 Panne/OK", key="p"+bid, use_container_width=True):
        ns = "libre" if s=="panne" else "panne"
        db.table("bornes").update({"statut":ns,"utilisateur":"","fin":""}).eq("id",bid).execute()
        st.rerun()

    with st.expander("📅 Réserver"):
        with st.form(key="f"+bid, clear_on_submit=True):
            n = st.text_input("Prénom")
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Déb", value=now.date(), key="d1"+bid)
            h1 = c1.selectbox("H.D", [f"{h:02d}:00" for h in range(24)], index=now.hour, key="h1"+bid)
            d2 = c2.date_input("Fin", value=now.date(), key="d2"+bid)
            h2 = c2.selectbox("H.F", [f"{h:02d}:00" for h in range(24)], index=(now.hour+1)%24, key="h2"+bid)
            if st.form_submit_button("OK"):
                if n:
                    t_res = f"{n} [{d1.strftime('%d/%m')} {h1} - {d2.strftime('%d/%m')} {h2}]"
                    old = b['suivant'] or ""
                    maj = f"{old} | {t_res}" if (old and old!="-") else t_res
                    db.table("bornes").update({"suivant":maj}).eq("id",bid).execute()
                    st.success("Pris !"); time.sleep(0.5); st.rerun()

    if b['suivant'] and b['suivant'].strip() not in ["", "-"]:
        for i in b['suivant'].split("|"):
            if i.strip(): st.caption(f"• {i.strip()}")
    st.divider()
