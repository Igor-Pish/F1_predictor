from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

DB_PATH = "sqlite:///f1_ui.db"

engine = create_engine(DB_PATH, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

def create_db():
    Base.metadata.create_all(engine)