import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz

# --- CONNEXION INSTANTANÉE ---
SUPABASE_URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
SUPABASE_KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Bornes Calais Pro", layout="wide")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- FONCTION : LIRE LES BORNES ---
def get_bornes():
    response = supabase.table("bornes").select("*").order("id").execute()
    return response.data

# --- FONCTION : MISE À JOUR ---
def update_borne(borne_id, data):
    supabase.table("bornes").update(data).eq("id", borne_id).execute()
    st.rerun()

st.title("⚡ Réseau Bornes Calais (Version Temps Réel)")

bornes = get_bornes()

for b in bornes:
    # Design de la carte
    couleur = "#d4edda" if b['statut'] == 'libre' else "#f8d7da"
    if b['statut'] == 'panne': couleur = "#fff3cd"
    
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:{couleur}; border:1px solid #ccc; color:black">
            <h3>🔌 {b['nom']}</h3>
            <p><b>Utilisateur :</b> {b['utilisateur'] or 'LIBRE'}</p>
            <p><b>Créneau :</b> {b['debut']} - {b['fin']}</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"🚩 Panne/OK", key=f"p_{b['id']}"):
            new_s = "libre" if b['statut'] == "panne" else "panne"
            update_borne(b['id'], {"statut": new_s, "utilisateur": "", "debut": "", "fin": ""})
            
    with c2:
        if b['statut'] == "occupé":
            if st.button(f"✅ Terminer", key=f"t_{b['id']}"):
                # Gestion automatique du suivant
                file = b['suivant'] or ""
                if "|" in file:
                    parts = file.split(" | ")
                    prochain = parts.pop(0)
                    update_borne(b['id'], {"utilisateur": prochain, "suivant": " | ".join(parts)})
                else:
                    update_borne(b['id'], {"statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""})

    # Réservation
    with st.expander("📅 Réserver"):
        with st.form(key=f"f_{b['id']}"):
            nom = st.text_input("Prénom")
            heure = st.text_input("Heure (ex: 14:00-16:00)")
            if st.form_submit_button("Valider"):
                if b['statut'] == "libre":
                    update_borne(b['id'], {"statut": "occupé", "utilisateur": nom, "debut": "Maintenant", "fin": heure})
                else:
                    # AJOUT À LA FILE (SANS ÉCRASER)
                    file_actuelle = b['suivant'] or ""
                    nouvelle_file = f"{file_actuelle} | {nom} ({heure})" if file_actuelle else f"{nom} ({heure})"
                    update_borne(b['id'], {"suivant": nouvelle_file})

    if b['suivant']:
        st.caption(f"📋 En attente : {b['suivant']}")
    st.divider()
