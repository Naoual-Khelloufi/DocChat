import streamlit as st
from core.auth.database import get_db
from core.auth.models import User
import sqlite3
def show_register():
    """Affiche le formulaire d'inscription sécurisé"""
    st.markdown("""
    <style>
        .register-box { max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="register-box">', unsafe_allow_html=True)
        st.header("Inscription")

        with st.form("register_form"):
            username = st.text_input("Nom d'utilisateur*", help="3 caractères minimum")
            email = st.text_input("Email (optionnel)")
            password = st.text_input("Mot de passe*", type="password")
            confirm = st.text_input("Confirmer le mot de passe*", type="password")
            
             #Option “Administrateur” visible seulement si l’admin actuellement connecté crée un compte
            make_admin = False
            if st.session_state.get("user", {}).get("role") == "admin":
                make_admin = st.checkbox("Créer comme Administrateur")

            
            if st.form_submit_button("Créer un compte"):
                if password != confirm:
                    st.error("Les mots de passe ne correspondent pas")
                    return False
                
                session = get_db()
                try:
                    # Créer l'utilisateur avec SQLAlchemy ORM
                    new_user = User(username=username, email=email, is_admin = make_admin)
                    new_user.set_password(password)  # Hash du mot de passe

                    session.add(new_user)
                    session.commit()
                    
                    st.success("Compte créé ! Connectez-vous maintenant")
                    return True

                except sqlite3.IntegrityError:
                    session.rollback()
                    st.error("Ce nom d'utilisateur existe déjà")
                    return False

                except Exception as e:
                    session.rollback()
                    st.error(f"Erreur inattendue : {str(e)}")
                    return False
        st.markdown('</div>', unsafe_allow_html=True)
    return False