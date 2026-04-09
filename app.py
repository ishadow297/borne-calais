import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz

# --- CONNEXION ---
URL = "https://bbdflpdeehgbgqqqdvnu.supabase.co"
KEY = "sb_publishable_APMQsSWxuWQ_r961_T8i6g_CeEe41Yz"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Bornes Calais Auto", layout="centered")
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)

# --- LOGIQUE DE PILOTAGE AUTOMATIQUE ---
def mettre_a_jour_statuts(bornes):
    for b in bornes:
        file = b.get('suivant') or ""
        if not file or file == "-":
            # Si aucune réservation, la borne est libre (sauf si en panne)
            if b['statut'] != "panne":
                supabase.table("bornes").update({"statut": "libre", "utilisateur": "", "fin": ""}).eq("id", b['id']).execute()
            continue
        
        reservations = [r.strip() for r in file.split("|") if r.strip()]
        nouvelle_file = []
        occupe_par = None
        heure_fin_occupe = ""
        a_change = False
        
        for res in reservations:
            try:
                # Format: "Nom [JJ/MM HH:MM - JJ/MM HH:MM]"
                nom_client = res.split(" [")[0]
                temps = res.split("[")[1].replace("]", "")
                debut_str, fin_str = temps.split(" - ")
                
                # Conversion en objets datetime
                dt_debut = datetime.strptime(f"{debut_str}/{now.year}", "%d/%m %H:%M/%Y").replace(tzinfo=tz)
                dt_fin = datetime.combine(dt_debut.date(), datetime.strptime(fin_str.split(" ")[1], "%H:%M").time()).replace(tzinfo=tz)
                # Correction si la fin est le lendemain du début
                if dt_fin < dt_debut: dt_fin += timedelta(days=1)

                # CAS 1 : C'est l'heure ! (Le créneau est en cours)
                if dt_debut <= now <= dt_fin:
                    occupe_par = nom_client
                    heure_fin_occupe = fin_str
                    nouvelle_file.append(res) # On le garde dans la liste tant qu'il charge
                
                # CAS 2 : C'est dans le futur
                elif dt_debut > now:
                    nouvelle_file.append(res)
                
                # CAS 3 : C'est passé
                else:
                    a_change = True # On ne l'ajoute pas à nouvelle_file, donc il est supprimé
            except:
                nouvelle_file.append(res)

        # MISE À JOUR BASE DE DONNÉES
        new_statut = b['statut']
        if b['statut'] != "panne":
            new_statut = "occupé" if occupe_par else "libre"
        
        supabase.table("bornes").update({
            "statut": new_statut,
            "utilisateur": occupe_par if occupe_par else "",
            "fin": heure_fin_occupe if occupe_par else "",
            "suivant": " | ".join(nouvelle_file)
        }).eq("id", b['id']).execute()

# --- CHARGEMENT ---
res = supabase.table("bornes").select("*").order("id").execute()
bornes = res.data
mettre_a_jour_statuts(bornes) # On lance l'automate avant d'afficher

st.title("⚡ Bornes Calais - Pilotage Automatique")
st.write(f"🕒 Heure actuelle : **{now.strftime('%d/%m %H:%M')}**")

for b in bornes:
    statut = str(b['statut']).lower()
    
    # Design Visuel
    if statut == "panne":
        st.error(f"❌ {b['nom']} : HORS SERVICE")
        color = "#ffcccc"
    elif statut == "occupé":
        color = "#f8d7da"
        status_txt = f"🔴 OCCUPÉ par {b['utilisateur']} (jusqu'à {b['fin']})"
    else:
        color = "#d4edda"
        status_txt = "🟢 DISPONIBLE"

    st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background-color:{color}; border:2px solid #666; color:black">
            <h3>{b['nom']}</h3>
            <p style="font-size:1.2em"><b>{status_txt}</b></p>
        </div>
    """, unsafe_allow_html=True)

    # 1. SIGNALER PANNE (Seul bouton manuel restant)
    if st.button(f"🚩 Signaler Panne / Réparée", key=f"p_{b['id']}"):
        nouveau = "libre" if statut == "panne" else "panne"
        supabase.table("bornes").update({"statut": nouveau}).eq("id", b['id']).execute()
        st.rerun()

    # 2. FORMULAIRE DE RÉSERVATION
    with st.expander("📅 Ajouter une réservation (Date + Heure)"):
        with st.form(key=f"f_{b['id']}", clear_on_submit=True):
            nom = st.text_input("Pr
