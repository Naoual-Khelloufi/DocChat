import streamlit as st
import sqlite3
from core.auth.database import get_db
from core.auth.models    import User
def show_register() -> bool:
    """
    Affiche le formulaire d'inscription
    et retourne True si l'inscription réussit.
    """

    # --- récupération sûre du rôle ------------------------------------
    current_user = st.session_state.get("user") or {}   # {} si None
    is_admin     = current_user.get("role") == "admin"

    st.markdown(
        """
        <style>.register-box{max-width:400px;margin:0 auto;padding:20px;
                             border:1px solid #ddd;border-radius:10px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    ok = False  # valeur de retour

    with st.container():
        st.markdown("<div class='register-box'>", unsafe_allow_html=True)
        st.header("Inscription")

        # ---------------------- FORMULAIRE ----------------------------
        with st.form("register_form"):
            username  = st.text_input("Nom d'utilisateur*", help="3 caractères minimum")
            email     = st.text_input("Email (optionnel)")
            password  = st.text_input("Mot de passe*", type="password")
            confirm   = st.text_input("Confirmer le mot de passe*", type="password")

            # ✅ case visible seulement pour un admin connecté
            make_admin = False
            if is_admin:
                make_admin = st.checkbox("Créer comme Administrateur")

            submitted = st.form_submit_button("Créer un compte")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------- TRAITEMENT -------------------------------
    if submitted:
        if password != confirm:
            st.error("Les mots de passe ne correspondent pas")
        else:
            session = get_db()
            try:
                user = User(username=username,
                            email=email,
                            is_admin=make_admin)
                user.set_password(password)
                session.add(user)
                session.commit()

                st.success("Compte créé ! Connectez-vous maintenant.")
                ok = True

            except sqlite3.IntegrityError:
                session.rollback()
                st.error("Ce nom d'utilisateur existe déjà")
            except Exception as exc:
                session.rollback()
                st.error(f"Erreur inattendue : {exc}")

    return ok
