from sqlalchemy.orm import Session
from .models import User
from .models import ChatHistory
from . import models
from .security import hash_password
from .models import Document
from sqlalchemy.exc import IntegrityError

#normalize email
def _norm_email(email: str) -> str:
    if not email or not email.strip():
        raise ValueError("Email is required")
    return email.strip().lower()

def create_user(db: Session, username: str, password: str, email: str = None):
    email_norm = _norm_email(email)
    try:
        db_user = User(username=username, email=email_norm, is_admin = False)
        db_user.set_password(password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already in use")

def update_user_email(db: Session, user_id: int, new_email: str):
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    user.email = _norm_email(new_email)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already in use")

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

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def save_chat_history(db: Session, user_id: int, question: str, answer: str):
    history = ChatHistory(user_id=user_id, question=question, answer=answer)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def save_message(
    db: Session,
    user_id: int,
    question: str,
    answer: str,
    document_id: int | None = None,
):
    """
    Insert a row into chat_history and return it.

    Args:
        user_id     : user identifier
        question    : question text
        answer      : generated answer
        document_id : associated PDF id (None if none)
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

def delete_message(db: Session, message_id: int, owner_id: int):
    """Delete a row from chat_history if it belongs to the user."""
    msg = db.get(ChatHistory, message_id)
    if msg and msg.user_id == owner_id:
        db.delete(msg)
        db.commit()

def get_user_history(db: Session, user_id: int, limit: int = 10):
    return db.query(ChatHistory)\
             .filter(ChatHistory.user_id == user_id)\
             .order_by(ChatHistory.timestamp.desc())\
             .limit(limit).all()

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

def delete_user_and_data(db: Session, user_id: int) -> None:
    """Delete the user together with their documents and chat history."""
    
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

