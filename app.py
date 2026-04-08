import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bornes Calais", page_icon="⚡")

# Lien de ton Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/gviz/tq?tqx=out:csv"
# Lien pour que les gens puissent MODIFIER
EDIT_URL = "https://docs.google.com/spreadsheets/d/1GbbDFFZxvGyy6umuoM4v3LuaOHItAdcydeWNxsz5blo/edit"

st.title("⚡ Planning des Bornes")
st.write("Consultez l'état des bornes ci-dessous. Pour réserver un créneau (aujourd'hui ou demain), utilisez le bouton modifier.")

# Lecture des données (Gratuit et simple)
try:
    df = pd.read_csv(SHEET_URL)
    # On affiche chaque borne proprement
    for index, row in df.iterrows():
        with st.container():
            col1, col2 = st.columns([2, 1])
            status = str(row['Statut']).strip().lower()
            icon = "🟢" if status == "libre" else "🔴"
            
            col1.subheader(f"{icon} {row['Borne']}")
            if status != "libre":
                col1.write(f"👤 Occupé par : **{row['Utilisateur']}**")
                col1.write(f"⏰ Fin prévue : **{row['Heure de fin']}**")
            
            if pd.notna(row['Suivant']) and str(row['Suivant']) != "":
                col1.info(f"📅 Réservations : {row['Suivant']}")
            
            st.divider()
except:
    st.error("Impossible de lire le planning pour le moment.")

# Le gros bouton magique
st.link_button("📝 MODIFIER LE PLANNING / RÉSERVER", EDIT_URL, use_container_width=True)

st.caption("Une fois que vous avez modifié le fichier Excel, rafraîchissez cette page pour voir les changements.")
