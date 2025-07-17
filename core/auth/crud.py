from sqlalchemy.orm import Session
from .models import User
from .models import ChatHistory

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

def get_user_history(db: Session, user_id: int, limit: int = 10):
    return db.query(ChatHistory)\
             .filter(ChatHistory.user_id == user_id)\
             .order_by(ChatHistory.timestamp.desc())\
             .limit(limit).all()
