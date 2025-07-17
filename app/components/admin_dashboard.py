import streamlit as st
from core.auth import crud, database

def render():
    st.title("🔧 Admin – Gestion des utilisateurs")

    db = database.SessionLocal()
    users = crud.list_users(db)

    for u in users:
        col1, col2 = st.columns([4, 1])
        badge = "🛡️ **Admin**" if u.is_admin else "👤 User"
        col1.markdown(f"**{u.username}** — {badge}")

        if not u.is_admin:
            if col2.button("❌ Supprimer", key=f"del-{u.id}"):
                crud.delete_user(db, u.id)
                st.experimental_rerun()


    if st.button("⬅️ Retour"):
        st.session_state.current_screen = "main_app"
        st.experimental_rerun()
