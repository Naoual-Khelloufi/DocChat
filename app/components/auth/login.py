import streamlit as st 
from core.auth.database import get_db
from core.auth.models import User

def show_login():
    db = get_db()  # Obtient une session SQLAlchemy
    try:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            
            if st.form_submit_button("Se connecter"):
                user = db.query(User).filter(User.username == username).first()
                
                if user and user.verify_password(password):
                    st.session_state.user = {
                        "id": user.id,
                        "username": user.username
                    }
                    st.success("Connexion réussie !")
                    return True
                else:
                    st.error("Identifiants incorrects")
        return False
    finally:
        db.close()  # Ferme proprement la session