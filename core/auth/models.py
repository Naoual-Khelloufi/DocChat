from sqlalchemy import Boolean, Column, Integer, String, DateTime
#from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base


Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_history")
    # 🆕  document_id stocke le fichier utilisé (nullable)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

class Document(Base):
    __tablename__ = "documents"
    id          = Column(Integer, primary_key=True)
    owner_id    = Column(Integer, ForeignKey("users.id"), nullable = False)
    path        = Column(String)
    title       = Column(String)
    uploaded = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

##############
    #Add admin flag
    is_admin = Column(Boolean, default=False)
    
    chat_history = relationship("ChatHistory", back_populates="user")


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

########
__all__ = ["Base", "User"]