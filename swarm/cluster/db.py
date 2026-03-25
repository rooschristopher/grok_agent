import os
from sqlalchemy import create_engine, Column, String, ForeignKey, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class NodeDB(Base):
    __tablename__ = "nodes"
    id = Column(String(36), primary_key=True, index=True)
    status = Column(String(20), default="idle")

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(500))
    status = Column(String(20), default="pending")
    node_id = Column(String(36), ForeignKey("nodes.id"), nullable=True)
    history_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=func.now())

engine = create_engine(f"sqlite:///{os.path.join(os.path.dirname(__file__), 'cluster.db')}", echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()