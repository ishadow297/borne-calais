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
heure_actuelle_str = now.strftime("%H:%M")

# --- FONCTION DE NETTOYAGE AUTOMATIQUE ---
def nettoyer_reservations_passees(bornes):
    for b in bornes:
        file = b.get('suivant') or ""
        if not file or file == "-": continue
        
        reservations = [r.strip() for r in file.split("|") if r.strip()]
        nouvelle_file = []
        modifie = False
        
        for res in reservations:
            try:
                # On cherche l'heure de fin dans le format "Nom (14:00-15:00)"
                # On extrait ce qui est entre le '-' et la parenthèse fermante
                heure_fin_str = res.split("-")[1].replace(")", "").strip()
                
                # Comparaison des heures
                if heure_fin_str > heure_actuelle_str:
                    nouvelle_file.append(res)
                else:
                    modifie = True # Cette réservation est passée, on ne l'ajoute pas
            except:
                nouvelle_file.append(res) # En cas d'erreur de format, on garde par sécurité
        
        if modifie:
            # On met à jour la file d'attente dans Supabase
            maj_file = " | ".join(nouvelle_file) if nouvelle_file else ""
            supabase.table("bornes").update({"suivant": maj_file}).eq("id", b['id']).execute()

# --- CHARGEMENT ---
res = supabase.table("bornes").select("*").order("id").execute()
bornes = res.data

# Lancer le nettoyage automatique dès l'ouverture
nettoyer_reservations_passees(bornes)

st.title("⚡ Bornes Calais - Réservations")
st.info(f"🕒 Heure actuelle : **{heure_actuelle_str}** (Les créneaux passés sont auto-supprimés)")

for b in bornes:
    statut = str(b['statut']).lower()
    
    # Design selon statut
    color = "#d4edda" if statut == "libre" else "#f8d7da"
    if statut == "panne": color = "#ffcccc"
    
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background-color:{color}; border:2px solid #999; color:black">
            <h3>📍 {b['nom']}</h3>
            <p><b>Statut :</b> {statut.upper()}</p>
            <p><b>Utilisateur actuel :</b> {b['utilisateur'] or 'Personne'}</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. ACTION : RESERVER UN CRÉNEAU
    with st.expander("📅 Réserver un créneau futur"):
        with st.form(key=f"res_{b['id']}", clear_on_submit=True):
            nom = st.text_input("Votre nom")
            col1, col2 = st.columns(2)
            h_debut = col1.selectbox("Début", [f"{h:02d}:00" for h in range(24)] + [f"{h:02d}:30" for h in range(24)], index=16)
            h_fin = col2.selectbox("Fin", [f"{h:02d}:00" for h in range(24)] + [f"{h:02d}:30" for h in range(24)], index=18)
            
            if st.form_submit_button("Ajouter au planning"):
                if nom and h_debut < h_fin:
                    nouveau_creneau = f"{nom} ({h_debut}-{h_fin})"
                    file_actuelle = b['suivant'] or ""
                    
                    # On ajoute à la file d'attente
                    if not file_actuelle or file_actuelle == "-":
                        maj = nouveau_creneau
                    else:
                        maj = f"{file_actuelle} | {nouveau_creneau}"
                    
                    supabase.table("bornes").update({"suivant": maj}).eq("id", b['id']).execute()
                    st.success(f"Réservé pour {nom}")
                    st.rerun()
                else:
                    st.error("L'heure de fin doit être après l'heure de début.")

    # 2. ACTION : BRANCHER MAINTENANT
    if statut == "libre":
        if st.button(f"🔌 Se brancher sur {b['nom']}", key=f"now_{b['id']}"):
            supabase.table("bornes").update({
                "statut": "occupé", 
                "utilisateur": "Branchement direct",
                "heure_branchement": heure_actuelle_str
            }).eq("id", b['id']).execute()
            st.rerun()

    # 3. ACTION : LIBERER / PANNE
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚩 Panne", key=f"hs_{b['id']}"):
            supabase.table("bornes").update({"statut": "panne"}).eq("id", b['id']).execute()
            st.rerun()
    with c2:
        if statut != "libre":
            if st.button("✅ Libérer la borne", key=f"free_{b['id']}"):
                supabase.table("bornes").update({
                    "statut": "libre", "utilisateur": "", "heure_branchement": ""
                }).eq("id", b['id']).execute()
                st.rerun()

    # Affichage de la file d'attente
    if b['suivant'] and b['suivant'] != "-":
        st.write("📋 **Planning des réservations :**")
        for r in b['suivant'].split("|"):
            st.caption(f"• {r.strip()}")
            
    st.divider()
