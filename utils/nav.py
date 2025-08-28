import streamlit as st

def navigate(screen: str, **extra_params):
    """Met à jour l'écran courant ET les query params, puis rerun."""
    st.session_state.current_screen = screen
    qp = {"screen": screen}
    qp.update(extra_params)
    st.query_params.from_dict(qp)
    st.rerun()