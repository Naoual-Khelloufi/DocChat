from collections import defaultdict
import streamlit as st
from core.auth import crud, database
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select
from reporting.db import SessionLocal as RepSession, Event, init_db


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

def _load_reporting_df(date_from, date_to, event_types=None, user_filter=""):
    init_db()
    from datetime import datetime as dt
    with RepSession() as s:
        q = select(Event).where(
            Event.created_at >= dt.combine(date_from, dt.min.time()),
            Event.created_at <  dt.combine(date_to + timedelta(days=1), dt.min.time()),
        )
        if event_types:
            q = q.where(Event.event_type.in_(event_types))
        if user_filter.strip():
            q = q.where(Event.user_id == user_filter.strip())
        rows = s.execute(q).scalars().all()

    data = [{
        "created_at": r.created_at,
        "event_type": r.event_type,
        "user_id": r.user_id,
        "status": r.status,
        "latency_ms": r.latency_ms,
        "tokens_in": r.tokens_in,
        "tokens_out": r.tokens_out,
        "score": r.score,
        "feedback": r.feedback,
        "filename": (r.payload or {}).get("filename"),
        "doc_ids": (r.payload or {}).get("doc_ids"),
        "doc_id": (r.payload or {}).get("doc_id"),
    } for r in rows]
    return pd.DataFrame(data)

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
    st.header("📊 Reporting — Statistiques d’utilisation & interactions")

    # Guard admin (au cas où)
    user = st.session_state.get("user")
    if not user or user.get("role") != "admin":
        st.error("Accès refusé : administrateur requis.")
        st.stop()

    today = datetime.utcnow().date()
    date_from = st.date_input("Du", today - timedelta(days=7), key="rep_from")
    date_to   = st.date_input("Au", today, key="rep_to")
    evt_types = st.multiselect("Types d'événements",
                           ["query","upload","feedback","error"],
                           default=["query","upload","feedback"], key="rep_types")
    user_filter = st.text_input("User ID (optionnel)", key="rep_user")

    df = _load_reporting_df(date_from, date_to, evt_types, user_filter)

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Événements", int(len(df)))
    colB.metric("Requêtes", int((df.event_type == "query").sum() if not df.empty else 0))
    errors_count = 0 if df.empty else int(((df.status == "error") | (df.event_type == "error")).sum())
    colC.metric("Erreurs", errors_count)
    lat_avg = 0 if df.empty or df["latency_ms"].isna().all() else float(df["latency_ms"].mean())
    colD.metric("Latence moyenne", f"{lat_avg:.0f} ms")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Volume par jour")
        if df.empty:
            st.info("Aucune donnée.")
        else:
            daily = df.groupby(df["created_at"].dt.date).size().reset_index(name="events")
            st.line_chart(daily.set_index("created_at"))

    with c2:
        st.subheader("Top utilisateurs (requêtes)")
        if df.empty:
            st.info("Aucune donnée.")
        else:
            topu = (df[df.event_type == "query"].groupby("user_id").size().sort_values(ascending=False).head(10))
            if topu.empty: 
                st.info("Aucune requête.")
            else:          
                st.bar_chart(topu)

    with c3:
        st.subheader("Feedback")
        if df.empty:
            st.info("Aucune donnée.")
        else:
            fb = df[df["feedback"].notna()].groupby("feedback").size().rename("count")
            if fb.empty: 
                st.info("Aucun feedback.")
            else:        
                st.bar_chart(fb)

    st.subheader("Détails (export CSV)")
    if df.empty:
        st.info("Rien à afficher.")
    else:
        st.dataframe(df.sort_values("created_at", ascending=False), use_container_width=True)
        st.download_button("Télécharger CSV", df.to_csv(index=False), "reporting.csv")

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
