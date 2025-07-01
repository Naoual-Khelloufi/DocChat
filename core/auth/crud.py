from sqlalchemy.orm import Session
from .models import User

def create_user(db: Session, username: str, password: str, email: str = None):
    db_user = User(username=username, email=email)
    db_user.set_password(password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()