import streamlit as st
import sqlite3
from core.auth.database import get_db
from core.auth.models    import User
from pathlib import Path
import base64
import mimetypes

#-----Style-------
def _load_css(path: str = "assets/style-register.css"):
        p = Path(path)
        if p.exists():
            st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
# Helper to add for _load_css
def _img_data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"
#-------------------

def show_register() -> bool:
    """
    Display the registration form.
    Return True if the registration succeeds.
    """
    # --- Initial configuration ---
    current_user = st.session_state.get("user") or {}
    is_admin = current_user.get("role") == "admin"
    ok = False  # return value

    # --- Style integration ---
    _load_css()
    logo_src = _img_data_uri("assets/logo_1.png")
    st.markdown(
        f"""
        <div class="login-logo">
            <img src="{logo_src}" alt="DocChat Logo"/>
        </div>
        """,
        unsafe_allow_html=True
    )
    # --- Principal content ---
    with st.container():
        st.markdown("<div class='register-container'>", unsafe_allow_html=True)
        st.markdown("<div class='register-title'><h1>Inscription</h1></div>", unsafe_allow_html=True)
        with st.form("register_form"):
            username = st.text_input(" ", placeholder="Nom d'utilisateur*", key="reg_user")
            email = st.text_input(" ", placeholder="Email*", key="reg_email")
            password = st.text_input(" ", placeholder="Mot de passe*", type="password", key="reg_pass")
            confirm = st.text_input(" ", placeholder="Confirmer le mot de passe*", type="password", key="reg_conf")

            # Admin checkbox only visible to admins
            make_admin = st.checkbox("Créer comme Administrateur") if is_admin else False

            submitted = st.form_submit_button("Créer un compte")

    # --- Processing ---
    if submitted:
        if not username:
            st.error("Le nom d'utilisateur est obligatoire")
        elif not password:
            st.error("Le mot de passe est obligatoire")
        elif password != confirm:
            st.error("Les mots de passe ne correspondent pas")
        else:
            session = get_db()
            try:
                user = User(
                    username=username,
                    email=email,
                    is_admin=make_admin
                )
                user.set_password(password)
                session.add(user)
                session.commit()

                st.success("Compte créé avec succès!")
                ok = True

            except sqlite3.IntegrityError:
                session.rollback()
                st.error("Ce nom d'utilisateur existe déjà")
            except Exception as e:
                session.rollback()
                st.error(f"Erreur: {str(e)}")
                
    return ok