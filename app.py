import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pytz, time

# --- CONFIG ---
U, K = "https://bbdflpdeehgbgqqqdvnu.supabase.co", "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
T = "bornes"

try:
    db = create_client(U, K)
except:
    st.error("Erreur DB"); st.stop()

st.set_page_config(page_title="Bornes Calais")
tz, fmt = pytz.timezone('Europe/Paris'), "%d/%m/%Y %H:%M"
now = datetime.now(tz)

# Traduction jours/mois
js = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
ms = ["Janv.","Févr.","Mars","Avril","Mai","Juin","Juil.","Août","Sept.","Oct.","Nov.","Déc."]
d_fr = f"{js[now.weekday()]} {now.day} {ms[now.month-1]}"

def auto(data):
    for b in data:
        bid, f = str(b['id']), b.get('suivant') or ""
        if not f.strip() or f.strip() == "-":
            if b['statut'] not in ["panne", "libre"] and b['utilisateur'] != "Manuel":
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
        
        # --- LIGNE 50 RÉPARÉE (ÉCLATÉE) ---
        if b['statut'] != "panne" and b['utilisateur'] != "Manuel":
            upd = {
                "statut": "occupé" if u else "libre",
                "utilisateur": u or "",
                "fin": hf,
                "suivant": " | ".join(nf)
            }
            db.table(T).update(upd).eq("id", bid).execute()

st.title("⚡ Bornes Calais")
st.info(f"📅 **{d_fr}** | 🕒 **{now.strftime('%H:%M')}**")

try:
    d = db.table(T).select("*").order("id").execute().data
    auto(d)
    d = db.table(T).select("*").order("id").execute().data
except: d = []

for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    with st.container():
        st.subheader(f"📍 {b['nom']}")
        if s == "panne": st.error("❌ HORS SERVICE")
        elif s == "occupé": st.warning(f"🔴 {b['utilisateur']} (Fin: {b['fin']})")
        else: st.success("🟢 DISPONIBLE")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚩 Panne/OK", key="p"+bid, use_container_width=True):
                ns = "libre" if s == "panne" else "panne"
                db.table(T).update({"statut":ns,"utilisateur":"","fin":""}).eq("id",bid).execute()
                st.rerun()
        with c2:
            if s == "libre":
                if st.button("🚗 Occuper", key="o"+bid, use_container_width=True):
                    db.table(T).update({"statut":"occupé","utilisateur":"Manuel","fin":"--"}).eq("id",bid).execute()
                    st.rerun()
            else:
                if st.button("✅ Libérer", key="l"+bid, use_container_width=True):
                    db.table(T).update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
                    st.rerun()

    with st.expander("📅 Réserver prochainement"):
        with st.form(key="f"+bid, clear_on_submit=True):
            nom = st.text_input("Prénom")
            d_sel = st.date_input("Date", value=now.date(), min_value=now.date(), key="dt"+bid)
            h1 = st.selectbox("Début", [f"{h:02d}:00" for h in range(24)], index=now.hour)
            h2 = st.selectbox("Fin", [f"{h:02d}:00" for h in range(24)], index=(now.hour+1)%24)
            if st.form_submit_button("VALIDER"):
                if nom and h1 < h2:
                    js = d_sel.strftime('%d/%m')
                    txt = f"{nom} [{js} {h1} - {js} {h2}]"
                    old = b.get('suivant') or ""
                    maj = f"{old} | {txt}" if (old and old != "-") else txt
                    db.table(T).update({"suivant": maj}).eq("id", bid).execute()
                    st.success(f"Réservé le {js}")
                    time.sleep(1); st.rerun()

    p = b.get('suivant') or ""
    if p.strip() and p != "-":
        st.write("**Planning :**")
        for i in p.split("|"):
            if i.strip(): st.caption(f"🗓️ {i.strip()}")
    st.divider()

time.sleep(60); st.rerun()
