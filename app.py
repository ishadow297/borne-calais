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

st.set_page_config(page_title="Bornes")
tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] != "panne" and b['statut'] != "libre" and b['utilisateur'] != "Manuel":
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

st.title("⚡ Bornes")
try:
    res = db.table("bornes").select("*").order("id").execute()
    d = res.data
    auto(d)
    res = db.table("bornes").select("*").order("id").execute()
    d = res.data
except: d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    c = "#ffcccc" if s=="panne" else ("#f8d7da" if s=="occupé" else "#d4edda")
    m = f"{b['utilisateur']} ({b['fin']})" if s=="occupé" else s
    st.markdown(f'<div style="padding:10px;background:{c};color:black;border-radius:5px"><b>{b["nom"]}</b>: {m}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Panne/OK", key="p"+bid):
            ns = "libre" if s=="panne" else "panne"
            db.table("bornes").update({"statut":ns,"utilisateur":"","fin":""}).eq("id",bid).execute()
            st.rerun()
    with c2:
        if s == "libre":
            if st.button("Occuper", key="o"+bid):
                db.table("bornes").update({"statut":"occupé","utilisateur":"Manuel","fin":"--"}).eq("id",bid).execute()
                st.rerun()
        else:
            if st.button("Libérer", key="l"+bid):
                db.table("bornes").update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
                st.rerun()

    with st.expander("📅"):
        with st.form(key="f"+bid, clear_on_submit=True):
            n = st.text_input("Qui?")
            d1 = st.date_input("Le", value=now.date(), key="d1"+bid)
            h1 = st.selectbox("D", [f"{h:02d}:00" for h in range(24)], index=now.hour, key="h1"+bid)
            h2 = st.selectbox("F", [f"{h:02d}:00" for h in range(24)], index=(now.hour+1)%24, key="h2"+bid)
            if st.form_submit_button("OK"):
                if n:
                    txt = f"{n} [{d1.strftime('%d/%m')} {h1} - {d1.strftime('%d/%m')} {h2}]"
                    old = b['suivant'] or ""
                    maj = f"{old} | {txt}" if (old and old!="-") else txt
                    db.table("bornes").update({"suivant":maj}).eq("id",bid).execute()
                    st.rerun()

    if b['suivant'] and b['suivant'].strip() not in ["", "-"]:
        for i in b['suivant'].split("|"):
            if i.strip(): st.caption(i.strip())
    st.divider()

time.sleep(60)
st.rerun()
