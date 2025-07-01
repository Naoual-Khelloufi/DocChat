import streamlit as st
import sqlite3
from core.auth.models import User
from core.auth.database import get_db

def show_register():
    """Affiche le formulaire d'inscription"""
    st.markdown("""
    <style>
        .register-box { max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="register-box">', unsafe_allow_html=True)
        st.header("Inscription")

        with st.form("register_form"):
            username = st.text_input("Nom d'utilisateur", help="3 caractères minimum")
            email = st.text_input("Email (optionnel)")
            password = st.text_input("Mot de passe", type="password")
            confirm = st.text_input("Confirmer le mot de passe", type="password")
            
            if st.form_submit_button("Créer un compte"):
                if password != confirm:
                    st.error("Les mots de passe ne correspondent pas")
                    return False
                
                try:
                    new_user = User(username, password, email)
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                        (new_user.username, new_user.password_hash, new_user.email)
                    )
                    conn.commit()
                    st.success("Compte créé ! Connectez-vous maintenant")
                    return True
                except sqlite3.IntegrityError:
                    st.error("Ce nom d'utilisateur existe déjà")
                    return False
                finally:
                    conn.close()
        st.markdown('</div>', unsafe_allow_html=True)