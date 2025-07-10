from sqlalchemy.orm import Session
from .models import User
from .models import ChatHistory

def create_user(db: Session, username: str, password: str, email: str = None):
    db_user = User(username=username, email=email)
    db_user.set_password(password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def save_chat_history(db: Session, user_id: int, question: str, answer: str):
    history = ChatHistory(user_id=user_id, question=question, answer=answer)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def get_user_history(db: Session, user_id: int, limit: int = 10):
    return db.query(ChatHistory)\
             .filter(ChatHistory.user_id == user_id)\
             .order_by(ChatHistory.timestamp.desc())\
             .limit(limit).all()
