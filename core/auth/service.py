import os
import ssl
import smtplib
import hashlib
import secrets
import urllib.parse
from email.message import EmailMessage
from datetime import datetime, timedelta
import streamlit as st
from sqlalchemy.orm import Session
from core.auth.models import User, PasswordResetToken

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def build_link(token: str) -> str:
    base = st.secrets["app"].get("base_url", os.getenv("APP_BASE_URL", "http://localhost:8501"))
    q = urllib.parse.urlencode({"screen": "reset_password_confirm", "token": token})
    return f"{base}?{q}"

def _build_message(to_email: str, url: str) -> EmailMessage:
    cfg = st.secrets["smtp"]
    msg = EmailMessage()
    msg["Subject"] = "Réinitialiser votre mot de passe"
    msg["From"] = cfg.get("from", cfg["user"])
    msg["To"] = to_email
    msg["Reply-To"] = cfg.get("from", cfg["user"])
    msg.set_content(f"Bonjour,\n\nCliquez sur ce lien pour définir un nouveau mot de passe :\n{url}\n\nSi vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n")
    msg.add_alternative(f"""\
<html><body style="font-family:Arial,sans-serif;">
  <p>Bonjour,</p>
  <p>Cliquez sur le bouton ci-dessous pour définir un nouveau mot de passe :</p>
  <p><a href="{url}" style="background:#e74c3c;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;">Définir un nouveau mot de passe</a></p>
  <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
</body></html>""", subtype="html")
    return msg

def send_reset_email(to_email: str, url: str) -> None:
    cfg = st.secrets["smtp"]
    msg = _build_message(to_email, url)
    with smtplib.SMTP(cfg["host"], cfg.get("port", 587)) as server:
        if cfg.get("use_tls", True):
            server.starttls(context=ssl.create_default_context())
        server.login(cfg["user"], cfg["password"])
        server.send_message(msg)

def request_password_reset(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return  
    raw = secrets.token_urlsafe(32)
    rec = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw),
        expires_at=datetime.utcnow() + timedelta(minutes=60),
    )
    db.add(rec)
    db.commit()
    reset_url = build_link(raw)
    
    if st.secrets.get("env") == "dev":
        st.info(f"DEV reset link: {reset_url}")
    else:
        send_reset_email(user.email, reset_url)

def verify_reset_token(db: Session, raw_token: str):
    rec = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == _hash_token(raw_token)
    ).first()
    if not rec or rec.used_at or rec.expires_at < datetime.utcnow():
        return None
    return rec.user

def consume_reset_token(db: Session, raw_token: str) -> None:
    rec = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == _hash_token(raw_token)
    ).first()
    if rec:
        rec.used_at = datetime.utcnow()
        db.commit()
