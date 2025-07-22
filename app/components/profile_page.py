import streamlit as st
from core.auth import crud, database
from collections import defaultdict

def render():
    user = st.session_state.user
    st.header("👤 Mon profil")

    # ---- Formulaire édition -----------------------------------
    with st.form("edit_profile"):
        new_username = st.text_input("Nom d'utilisateur", value=user["username"])
        new_email    = st.text_input("Email", value=user.get("email") or "")
        new_password = st.text_input("Nouveau mot de passe", type="password")

        if st.form_submit_button("Enregistrer"):
            db = database.SessionLocal()
            crud.update_user(
                db,
                user_id=user["id"],
                username=new_username,
                email=new_email or None,
                password=new_password or None,   # ne change que si rempli
            )
            st.success("Profil mis à jour !")
            # mets à jour la session
            st.session_state.user["username"] = new_username
            st.session_state.user["email"] = new_email

    st.markdown("---")

    # ---- Historique personnel (dates + déroulé) ----------------
    st.subheader("🕒 Mon historique")

    db = database.SessionLocal()
    history = crud.get_user_history(db, user["id"])   # tout

    if not history:
        st.info("Aucun message enregistré.")
        return

    # Regroupement par date
    grouped = defaultdict(list)
    for h in history:
        grouped[h.timestamp.strftime("%Y-%m-%d")].append(h)

    dates = sorted(grouped.keys(), reverse=True)
    date_sel = st.selectbox("Choisir une date", ["📅 ---"] + dates, index=0)

    if date_sel != "📅 ---":
        for h in grouped[date_sel]:
            st.markdown(f"**🕑 {h.timestamp.strftime('%H:%M:%S')}**")
            st.markdown(f"**❓ Q :** {h.question}")
            st.markdown(f"**💬 R :** {h.answer}")
            st.markdown("-----")

    # Bouton retour
    if st.button("⬅️ Retour"):
        st.session_state.current_screen = "main_app"
        
