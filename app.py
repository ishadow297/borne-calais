import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz

# --- CONNEXION ---
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Bornes Calais Pro", layout="centered")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)
heure_actuelle = now.strftime("%H:%M")

# --- CHARGEMENT ---
res = supabase.table("bornes").select("*").order("id").execute()
bornes = res.data

st.title("⚡ Monitoring Bornes Calais")
st.write(f"🕒 Heure système : **{heure_actuelle}**")

for b in bornes:
    statut = str(b['statut']).lower()
    
    # --- DESIGN AMÉLIORÉ ---
    if statut == "panne":
        # Design Panne : Rouge clignotant / Alerte
        st.error(f"⚠️ LA BORNE '{b['nom']}' EST HORS SERVICE")
        bg_color = "#721c24" # Rouge foncé
        text_color = "white"
        status_msg = "❌ EN PANNE / RÉPARATION"
    elif statut == "occupé":
        bg_color = "#fff3cd" # Jaune
        text_color = "#856404"
        status_msg = f"⏳ OCCUPÉ par {b['utilisateur']}"
    else:
        bg_color = "#d4edda" # Vert
        text_color = "#155724"
        status_msg = "✅ DISPONIBLE"

    # Affichage de la carte
    st.markdown(f"""
        <div style="padding:20px; border-radius:15px; background-color:{bg_color}; color:{text_color}; border:2px solid {text_color}; margin-bottom:10px">
            <h2 style="margin:0">{b['nom']}</h2>
            <p style="font-size:1.3em; font-weight:bold; margin:5px 0">{status_msg}</p>
            <hr style="border:0.5px solid {text_color}">
            <p style="margin:0">🔌 <b>Branché à :</b> {b.get('heure_branchement') or '--:--'}</p>
            <p style="margin:0">📅 <b>Fin prévue :</b> {b['fin'] or '--:--'}</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        # Bouton Panne ultra visible
        if statut == "panne":
            if st.button(f"🔧 Signaler Réparée", key=f"fix_{b['id']}", use_container_width=True):
                supabase.table("bornes").update({"statut": "libre", "heure_debranchement": heure_actuelle}).eq("id", b['id']).execute()
                st.rerun()
        else:
            if st.button(f"🚩 Signaler PANNE", key=f"hs_{b['id']}", use_container_width=True):
                supabase.table("bornes").update({"statut": "panne", "utilisateur": "HS"}).eq("id", b['id']).execute()
                st.rerun()

    with col2:
        # Bouton Terminer
        if statut == "occupé":
            if st.button(f"🔌 Débrancher", key=f"end_{b['id']}", use_container_width=True):
                file = b['suivant'] or ""
                if "|" in file:
                    items = [i.strip() for i in file.split("|") if i.strip()]
                    prochain = items.pop(0)
                    # On passe au suivant et on enregistre son heure de branchement (maintenant)
                    supabase.table("bornes").update({
                        "utilisateur": prochain, 
                        "suivant": " | ".join(items),
                        "heure_branchement": heure_actuelle
                    }).eq("id", b['id']).execute()
                else:
                    # On libère et on enregistre l'heure de débranchement
                    supabase.table("bornes").update({
                        "statut": "libre", "utilisateur": "", "debut": "", "fin": "", 
                        "suivant": "", "heure_branchement": "", "heure_debranchement": heure_actuelle
                    }).eq("id", b['id']).execute()
                st.rerun()

    # Formulaire de Branchement
    if statut == "libre":
        with st.expander("📝 Brancher mon véhicule maintenant"):
            with st.form(key=f"f_{b['id']}"):
                nom = st.text_input("Votre Prénom")
                h_fin = st.selectbox("Heure de fin prévue", [f"{h:02d}:00" for h in range(24)])
                if st.form_submit_button("Lancer la charge"):
                    if nom:
                        supabase.table("bornes").update({
                            "statut": "occupé", 
                            "utilisateur": nom, 
                            "heure_branchement": heure_actuelle, 
                            "fin": h_fin
                        }).eq("id", b['id']).execute()
                        st.rerun()
    
    if b['suivant']:
        st.info(f"⏭️ Prochain en attente : {b['suivant']}")
    
    # Affichage discret du dernier débranchement
    if b.get('heure_debranchement'):
        st.caption(f"Dernière libération de cette borne à {b['heure_debranchement']}")
    
    st.divider()
