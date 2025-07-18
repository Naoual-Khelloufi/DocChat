from collections import defaultdict
import streamlit as st
from core.auth import crud, database

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
def _user_row(u):
    """Affiche une ligne utilisateur + boutons d'action."""
    col1, col2, col3 = st.columns([4, 1, 1])
    badge = "🛡️ **Admin**" if u.is_admin else "👤 User"
    # nom cliquable → détail
    if col1.button(f"**{u.username}** — {badge}", key=f"detail-{u.id}"):
        st.session_state.selected_user_id = u.id
    # bouton suppression (protège les admins)
    if not u.is_admin:
        if col2.button("❌ Supprimer", key=f"del-{u.id}"):
            return "delete"
    return None


def _user_detail(u):
    """Affiche la fiche détaillée d’un utilisateur sélectionné."""
    st.subheader(f"Détail de **{u.username}**")
    st.write(f"- **ID** : `{u.id}`")
    st.write(f"- **Email** : `{u.email or '—'}`")
    st.write(f"- **Rôle** : {'Admin' if u.is_admin else 'Utilisateur'}")
    st.write(f"- **Hash mot de passe** : `{u.password_hash}`")
    st.write(f"- **Créé le** : {u.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(u,'created_at') else 'N/A'}")
    st.markdown("---")

     # ─── 1. Récupérer tout l'historique ──────────────────────
    db = database.SessionLocal()
    history = crud.get_user_history(db, u.id)  # plus de limite

    if not history:
        st.info("Aucun historique trouvé.")
        return

    # ─── 2. Grouper par date (AAAA-MM-JJ) ────────────────────
    grouped = defaultdict(list)
    for h in history:
        grouped[h.timestamp.strftime("%Y-%m-%d")].append(h)

    # Trier les dates récentes d'abord
    dates_sorted = sorted(grouped.keys(), reverse=True)

    # ─── 3. Selectbox : aucune date pré-sélectionnée ───────────────────
    sel_key = f"selected_history_date_{u.id}"
    placeholder = "📅 Choisir une date"
    selected_date = st.selectbox(
        "Historique par date",
        options=[placeholder] + dates_sorted,
        index=0,
        key=sel_key,
    )

    # ─── 4. Afficher l’historique seulement si une vraie date est choisie ────────────
    if selected_date != placeholder:
        st.markdown(f"### 💬 Conversations du {selected_date}")
        for h in grouped[selected_date]:
            st.markdown(f"**🕑 {h.timestamp.strftime('%H:%M:%S')}**")
            st.markdown(f"**❓ Q :** {h.question}")
            st.markdown(f"**💬 R :** {h.answer}")
            st.markdown("-----")


# ------------------------------------------------------------------ #
# Page principale
# ------------------------------------------------------------------ #
def render():
    st.title("🔧 Admin – Gestion des utilisateurs")

    # Bouton retour
    if st.button("⬅️ Retour"):
        st.session_state.current_screen = "main_app"
        

    db = database.SessionLocal()

    # -------------------------------------- #
    # 1) Formulaire pour créer un nouvel admin
    # -------------------------------------- #
    with st.expander("➕ Créer un nouveau compte admin"):
        with st.form("create_admin_form"):
            new_username = st.text_input("Nom d'utilisateur")
            new_email = st.text_input("Email (optionnel)") # noqa: F841
            new_password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Créer"):
                if not new_username or not new_password:
                    st.error("Nom et mot de passe obligatoires.")
                else:
                    try:
                        crud.create_admin(db, new_username, new_password)
                        st.success(f"Compte admin **{new_username}** créé.")
                    except Exception as exc:
                        st.error(f"Erreur : {exc}")

    st.markdown("---")

    # -------------------------------------- #
    # 2) Liste et actions sur les utilisateurs
    # -------------------------------------- #
    users = crud.list_users(db)
    if "selected_user_id" not in st.session_state:
        st.session_state.selected_user_id = None

    for u in users:
        action = _user_row(u)
        if action == "delete":
            crud.delete_user(db, u.id)
            

        # Affiche la fiche si selectionnée
        if st.session_state.selected_user_id == u.id:
            _user_detail(u)
