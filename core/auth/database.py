#database managment
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.auth import models      # assure d’avoir Document, etc.



SQLALCHEMY_DATABASE_URL = "sqlite:///./data/users.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
models.Base.metadata.create_all(bind=engine)
#Base = declarative_base()


def get_db():
    return SessionLocal()