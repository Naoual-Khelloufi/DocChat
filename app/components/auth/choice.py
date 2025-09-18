import streamlit as st

def show_auth_choice():
    """Display the authentication choice card"""
    st.markdown("""
    <style>
        .auth-card {
            max-width: 500px;
            margin: 0 auto;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            text-align: center;
        }
        .auth-btn {
            width: 100%;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('### 🔒 Choisissez un mode d\'accès')
        
        if st.button("Se Connecter", key="login_btn", use_container_width=True):
            st.session_state.auth_action = "login"
        
        if st.button("S'Enregistrer", key="register_btn", use_container_width=True):
            st.session_state.auth_action = "register"
        
        if st.button("Continuer sans Compte", key="guest_btn", use_container_width=True):
            st.session_state.auth_action = "guest"
        
        st.markdown('</div>', unsafe_allow_html=True)