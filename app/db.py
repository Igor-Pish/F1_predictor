from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite файл лежит прямо в папке app/
DB_PATH = Path(__file__).resolve().parent / "f1_data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    connect_args={"check_same_thread": False},  # важно для SQLite при нескольких потоках/процессах
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def create_db() -> None:
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)