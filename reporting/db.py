from sqlalchemy import (create_engine, Column, Integer, String, Float, DateTime, JSON, Text)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DB_URL = os.getenv("REPORTING_DB_URL", "sqlite:///./reporting.db")
engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), index=True)         # query | upload | error
    user_id = Column(String(128), index=True, nullable=True)
    session_id = Column(String(128), index=True, nullable=True)
    status = Column(String(20), default="ok")
    latency_ms = Column(Float, nullable=True)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    score = Column(Float, nullable=True)
    #feedback = Column(String(10), nullable=True)        # up | down
    prompt = Column(Text, nullable=True)                # will be truncated by the logger
    response_summary = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

def init_db():
    Base.metadata.create_all(engine)