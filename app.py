import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pytz

# --- CONNEXION ---
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Bornes Calais Pro", layout="centered")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- FONCTION DE NETTOYAGE AUTOMATIQUE (MULTI-JOURS) ---
def nettoyer_planning(bornes):
    for b in bornes:
        file = b.get('suivant') or ""
        if not file or file == "-": continue
        
        reservations = [r.strip() for r in file.split("|") if r.strip()]
        nouvelle_file = []
        a_ete_modifie = False
        
        for res in reservations:
            try:
                # Format attendu : "Nom [JJ/MM HH:MM - JJ/MM HH:MM]"
                # On extrait la partie date de fin (après le '-')
                partie_fin = res.split("-")[1].replace("]", "").strip() # Ex: "10/04 15:30"
                date_fin = datetime.strptime(f"{partie_fin}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)
                
                # Si la date/heure de fin est encore dans le futur, on garde
                if date_fin > now:
                    nouvelle_file.append(res)
                else:
                    a_ete_modifie = True # Trop vieux, on supprime
            except:
                nouvelle_file.append(res) # Garder si format inconnu
        
        if a_ete_modifie:
            maj = " | ".join(nouvelle_file) if nouvelle_file else ""
            supabase.table("bornes").update({"suivant": maj}).eq("id", b['id']).execute()

# --- CHARGEMENT ---
res = supabase.table("bornes").select("*").order("id").execute()
bornes = res.data
nettoyer_planning(bornes)

st.title("⚡ Bornes Calais - Planning")
st.info(f"📅 Nous sommes le : **{now.strftime('%d/%m à %H:%M')}**")

for b in bornes:
    statut = str(b['statut']).lower()
    color = "#d4edda" if statut == "libre" else "#f8d7da"
    if statut == "panne": color = "#ffcccc"
    
    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background-color:{color}; border:2px solid #666; color:black">
            <h3>📍 {b['nom']}</h3>
            <p><b>Statut actuel :</b> {statut.upper()}</p>
            <p><b>Utilisateur :</b> {b['utilisateur'] or 'Libre'}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- FORMULAIRE DE RÉSERVATION MULTI-JOURS ---
    with st.expander("📅 Réserver un créneau (Plusieurs jours possibles)"):
        with st.form(key=f"res_{b['id']}", clear_on_submit=True):
            nom = st.text_input("Votre nom")
            
            c1, c2 = st.columns(2)
            d_debut = c1.date_input("Date début", value=now.date())
            h_debut = c1.selectbox("Heure début", [f"{h:02d}:00" for h in range(24)], key=f"hd_{b['id']}")
            
            d_fin = c2.date_input("Date fin", value=now.date() + timedelta(days=1))
            h_fin = c2.selectbox("Heure fin", [f"{h:02d}:00" for h in range(24)], key=f"hf_{b['id']}")
            
            if st.form_submit_button("Enregistrer la réservation"):
                if nom:
                    # Construction du texte de réservation
                    txt_debut = f"{d_debut.strftime('%d/%m')} {h_debut}"
                    txt_fin = f"{d_fin.strftime('%d/%m')} {h_fin}"
                    nouveau_creneau = f"{nom} [{txt_debut} - {txt_fin}]"
                    
                    file_actuelle = b['suivant'] or ""
                    maj = f"{file_actuelle} | {nouveau_creneau}" if (file_actuelle and file_actuelle != "-") else nouveau_creneau
                    
                    supabase.table("bornes").update({"suivant": maj}).eq("id", b['id']).execute()
                    st.success("Réservation enregistrée !")
                    st.rerun()

    # --- ACTIONS RESTANTES ---
    c1, c2 = st.columns(2)
    with c1:
        # Bouton Panne (Visible pour tous pour signaler un souci)
        label_panne = "🔧 Signaler Réparée" if statut == "panne" else "🚩 Signaler PANNE"
        if st.button(label_panne, key=f"panne_{b['id']}", use_container_width=True):
            nouveau_statut = "libre" if statut == "panne" else "panne"
            supabase.table("bornes").update({"statut": nouveau_statut}).eq("id", b['id']).execute()
            st.rerun()
            
    with c2:
        # Bouton Se Brancher (Uniquement si libre)
        if statut == "libre":
            if st.button("🔌 Se brancher maintenant", key=f"run_{b['id']}", use_container_width=True):
                supabase.table("bornes").update({
                    "statut": "occupé", 
                    "utilisateur": "Branchement Direct",
                    "heure_branchement": now.strftime("%H:%M")
                }).eq("id", b['id']).execute()
                st.rerun()

    # --- AFFICHAGE DU PLANNING ---
    if b['suivant'] and b['suivant'] != "-":
        st.write("📋 **Planning des prochains jours :**")
        reservations = b['suivant'].split("|")
        for r in reservations:
            st.write(f"• {r.strip()}")
            
    st.divider()
