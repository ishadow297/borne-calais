import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import pytz
import time

# --- 1. CONFIGURATION CONNEXION ---
# Remplace par tes vraies clés Supabase (Dashboard > Settings > API)
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erreur de configuration Supabase : {e}")
    st.stop()

st.set_page_config(page_title="Bornes Calais Live", layout="wide")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- 2. FONCTION DE CHARGEMENT ---
def load_data():
    try:
        # On récupère les données
        res = supabase.table("bornes").select("*").order("id").execute()
        return res.data
    except Exception as e:
        st.error(f"Erreur lors de la lecture de la table 'bornes' : {e}")
        st.info("Vérifie que la table existe et que le RLS est désactivé.")
        return []

# --- 3. TRAITEMENT ET AFFICHAGE ---
st.title("⚡ Réseau de Bornes - Calais Pro")
st.write(f"📅 {now.strftime('%d/%m/%Y')} | 🕒 {now.strftime('%H:%M')}")

bornes = load_data()

# Si la table est vide
if not bornes:
    st.warning("⚠️ Aucune donnée trouvée. Ajoute une ligne dans ta table Supabase !")
    if st.button("Simuler une borne (Aide)"):
        st.info("Va sur Supabase > Table Editor > bornes > Insert row. Mets 'Borne 1' dans la colonne 'nom'.")
else:
    # On boucle sur chaque borne trouvée
    for b in bornes:
        # Détermination de la couleur selon le statut
        statut = str(b.get('statut', 'libre')).lower()
        bg_color = "#d4edda" if statut == "libre" else "#f8d7da"
        if statut == "panne": bg_color = "#fff3cd"

        # Affichage de la carte
        st.markdown(f"""
            <div style="padding:20px; border-radius:15px; background:{bg_color}; border:2px solid #bbb; color:black; margin-bottom:10px">
                <h2 style="margin:0">📍 {b['nom']}</h2>
                <p style="font-size:1.2em; margin:5px 0"><b>Utilisateur :</b> {b['utilisateur'] or 'DISPONIBLE'}</p>
                <p style="margin:0"><b>Session :</b> {b['debut'] or '--'} ⮕ {b['fin'] or '--'}</p>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        
        with c1:
            # Gestion Panne
            btn_hs = "🔧 Réparée" if statut == "panne" else "🚩 Signaler Panne"
            if st.button(btn_hs, key=f"hs_{b['id']}", use_container_width=True):
                new_s = "libre" if statut == "panne" else "panne"
                supabase.table("bornes").update({"statut": new_s, "utilisateur": "", "debut": "", "fin": ""}).eq("id", b['id']).execute()
                st.rerun()

        with c2:
            # Gestion Libération
            if statut == "occupé":
                if st.button("✅ Terminer Charge", key=f"end_{b['id']}", use_container_width=True):
                    file = b['suivant'] or ""
                    if "|" in file:
                        items = [i.strip() for i in file.split("|") if i.strip()]
                        prochain = items.pop(0)
                        supabase.table("bornes").update({
                            "utilisateur": prochain, 
                            "suivant": " | ".join(items),
                            "debut": b['fin']
                        }).eq("id", b['id']).execute()
                    else:
                        supabase.table("bornes").update({"statut": "libre", "utilisateur": "", "debut": "", "fin": "", "suivant": ""}).eq("id", b['id']).execute()
                    st.rerun()

        # Formulaire de réservation
        with st.expander("📝 Réserver ou Prendre la place"):
            with st.form(key=f"form_{b['id']}", clear_on_submit=True):
                nom = st.text_input("Prénom")
                heure_fin = st.selectbox("Heure de fin prévue", [f"{h:02d}:00" for h in range(24)] + [f"{h:02d}:30" for h in range(24)])
                
                if st.form_submit_button("Confirmer"):
                    if nom:
                        if statut == "libre":
                            supabase.table("bornes").update({
                                "statut": "occupé", 
                                "utilisateur": nom, 
                                "debut": now.strftime("%H:%M"), 
                                "fin": heure_fin
                            }).eq("id", b['id']).execute()
                        else:
                            old_file = b['suivant'] or ""
                            new_entry = f"{nom} ({heure_fin})"
                            new_file = f"{old_file} | {new_entry}" if old_file else new_entry
                            supabase.table("bornes").update({"suivant": new_file}).eq("id", b['id']).execute()
                        st.rerun()

        if b['suivant']:
            st.caption(f"📋 En attente : {b['suivant']}")
        st.divider()
