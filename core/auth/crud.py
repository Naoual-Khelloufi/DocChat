from sqlalchemy.orm import Session
from .models import User
from .models import ChatHistory
from . import models
from .security import hash_password
from .models import Document


def create_user(db: Session, username: str, password: str, email: str = None):
    db_user = User(username=username, email=email, is_admin = False)
    db_user.set_password(password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

###########
def create_admin(db: Session, username: str, password: str, email: str = None):
    db_admin = User(username=username, email=email, is_admin = True)
    db_admin.set_password(password)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin
#for admin 
def list_users(db):
    return db.query(User).all()

def delete_user(db, user_id: int):
    db_user = db.get(User, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()

########
def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def save_chat_history(db: Session, user_id: int, question: str, answer: str):
    history = ChatHistory(user_id=user_id, question=question, answer=answer)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

# ----------------------------------------------------------------------
#  Enregistrer une question / réponse  (+ document_id optionnel)
# ----------------------------------------------------------------------
def save_message(
    db: Session,
    user_id: int,
    question: str,
    answer: str,
    document_id: int | None = None,
):
    """
    Insère une ligne dans chat_history et la renvoie.

    Args:
        user_id      : identifiant de l'utilisateur
        question     : texte de la question
        answer       : réponse générée
        document_id  : id du PDF associé (None si aucun)
    """
    msg = ChatHistory(
        user_id     = user_id,
        question    = question,
        answer      = answer,
        document_id = document_id,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# --- Suppression d’un message d’historique -----------------------------
def delete_message(db: Session, message_id: int, owner_id: int):
    """Supprime une ligne de chat_history si elle appartient à l’utilisateur."""
    msg = db.get(ChatHistory, message_id)
    if msg and msg.user_id == owner_id:
        db.delete(msg)
        db.commit()


def get_user_history(db: Session, user_id: int, limit: int = 10):
    return db.query(ChatHistory)\
             .filter(ChatHistory.user_id == user_id)\
             .order_by(ChatHistory.timestamp.desc())\
             .limit(limit).all()

#def update_user(db, user_id: int, username: str | None = None,
#                email: str | None = None, password: str | None = None):
#    user = db.get(User, user_id)
#    if not user:
#        raise ValueError("Utilisateur introuvable")
#    if username:
#        user.username = username
#    if email is not None:          # peut être chaîne vide → None
#        user.email = email
#    if password:
#        user.set_password(password)
#    db.commit()

# --- Fonctions Document --------------------------------------------------
def save_document(db, owner_id: int, title: str, path: str) -> models.Document:
    doc = models.Document(owner_id=owner_id, title=title, path=path)
    db.add(doc) 
    db.commit()
    return doc

def list_user_documents(db, owner_id: int):
    return (db.query(models.Document)
             .filter(models.Document.owner_id == owner_id)
             .order_by(models.Document.uploaded.desc())
             .all())

def delete_document(db, doc_id: int, owner_id: int):
    doc = db.get(models.Document, doc_id)
    if doc and doc.owner_id == owner_id:
        db.delete(doc) 
        db.commit()

# --- Mise à jour profil --------------------------------------------------
def update_user(db, user_id: int, username=None, email=None, password=None):
    user = db.get(models.User, user_id)
    if not user:
        raise ValueError("Utilisateur introuvable")
    if username:
        user.username = username
    if email is not None:
        user.email = email
    if password:
        user.password_hash = hash_password(password)
    db.commit()

#  Suppression définitive d’un utilisateur et de ses données
def delete_user_and_data(db: Session, user_id: int) -> None:
    """Efface l’utilisateur + ses documents + son historique."""
    # documents 
    (db.query(Document)
       .filter(Document.owner_id == user_id)
       .delete(synchronize_session=False))

    # historique
    (db.query(ChatHistory)
       .filter(ChatHistory.user_id == user_id)
       .delete(synchronize_session=False))

    # utilisateur
    user = db.get(User, user_id)
    if user:
        db.delete(user)

    db.commit()

