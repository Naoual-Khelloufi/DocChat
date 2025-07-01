import streamlit as st
from core.auth.database import get_db
from core.auth.models import User

def show_login():
    """Affiche le formulaire de connexion"""
    st.markdown("""
    <style>
        .login-box { max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.header("Connexion")

        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            
            if st.form_submit_button("Se connecter"):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                conn.close()

                if result and User.verify_password(result[0], password):
                    st.session_state.user = {"username": username}
                    st.success("Connecté avec succès !")
                    return True
                else:
                    st.error("Identifiants incorrects")
                    return False
        st.markdown('</div>', unsafe_allow_html=True)