with col1:
    st.write(f"### {row['Borne']}")
    st.write(f"{icon} **{row['Statut'].upper()}**{info_user}")
    # On affiche si quelqu'un a déjà réservé le tour d'après
    if pd.notna(row['Suivant']) and row['Suivant'] != "":
        st.warning(f"⏳ Prochain : {row['Suivant']}")

with col2:
    if status == "libre":
        # ... (ton code actuel pour réserver quand c'est libre) ...
    else:
        # Si c'est occupé, on propose de réserver le tour suivant
        nom_suivant = st.text_input("Réserver après ?", key=f"next_{index}", placeholder="Ton nom")
        if st.button("Se mettre en attente", key=f"btn_next_{index}"):
            df.at[index, 'Suivant'] = nom_suivant
            conn.update(spreadsheet=url, data=df)
            st.success("C'est noté, tu es le prochain !")
            st.rerun()
            
        if st.button("Libérer la borne", key=f"lib_{index}"):
            # Quand on libère, si quelqu'un attendait, il peut devenir le statut principal
            df.at[index, 'Statut'] = "libre"
            df.at[index, 'Utilisateur'] = ""
            df.at[index, 'Heure de fin'] = ""
            # Optionnel : On pourrait basculer le 'Suivant' en 'Utilisateur' ici
            conn.update(spreadsheet=url, data=df)
            st.rerun()
