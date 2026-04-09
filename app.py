import streamlit as st
from supabase import create_client
from datetime import datetime
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

# Traduction française manuelle
js = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
ms = ["Janv.","Févr.","Mars","Avril","Mai","Juin","Juil.","Août","Sept.","Oct.","Nov.","Déc."]
d_fr = f"{js[now.weekday()]} {now.day} {ms[now.month-1]}"

# --- AUTOMATE DE GESTION ---
def auto(data):
    for b in data:
        bid = str(b['id'])
        f = b.get('suivant') or ""
        # Si aucun planning, on libère la borne (sauf si Manuel ou Panne)
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
                elif dd > now:
                    nf.append(r)
            except:
                nf.append(r)
        
        # Mise à jour auto du statut selon le planning
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

# Lecture des données
try:
    res = db.table(T).select("*").order("id").execute()
    d = res.data
    auto(d) # Lance l'automate
    # Re-lecture après automate
    d = db.table(T).select("*").order("id").execute().data
except Exception as e:
    st.error(f"Erreur de lecture : {e}")
    d = []

# Boucle d'affichage des bornes
for b in d:
    bid, s = str(b['id']), str(b['statut']).lower()
    
    with st.container():
        st.subheader(f"📍 {b['nom']}")
        
        # Affichage du statut avec couleurs natives
        if s == "panne":
            st.error("❌ HORS SERVICE (PANNE)")
        elif s == "occupé":
            st.warning(f"🔴 OCCUPÉ par {b['utilisateur']} (Fin: {b['fin']})")
        else:
            st.success("🟢 DISPONIBLE")

        # Boutons d'action rapides
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚩 Signal. Panne", key="p"+bid, use_container_width=True):
                ns = "libre" if s == "panne" else "panne"
                db.table(T).update({"statut":ns,"utilisateur":"","fin":""}).eq("id",bid).execute()
                st.rerun()
        with c2:
            if s == "libre":
                if st.button("🚗 Occuper (Manuel)", key="o"+bid, use_container_width=True):
                    db.table(T).update({"statut":"occupé","utilisateur":"Manuel","fin":"--"}).eq("id",bid).execute()
                    st.rerun()
            else:
                if st.button("✅ Libérer Borne", key="l"+bid, use_container_width=True):
                    db.table(T).update({"statut":"libre","utilisateur":"","fin":""}).eq("id",bid).execute()
                    st.rerun()
