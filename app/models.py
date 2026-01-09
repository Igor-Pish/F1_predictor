from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Index

Base = declarative_base()

class SessionMetric(Base):
    __tablename__ = "session_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    year = Column(Integer, index=True, nullable=False)
    round = Column(Integer, index=True, nullable=False)
    session = Column(String, index=True, nullable=False)  # FP1/FP2/FP3/Q/R/S/SQ

    driver = Column(String, index=True, nullable=False)   # аббревиатура (VER, HAM, ...)
    team = Column(String, nullable=True)

    best_lap = Column(Float, nullable=True)   # сек
    laps = Column(Integer, nullable=True)
    main_compound = Column(String, nullable=True)

    position = Column(Integer, nullable=True)
    q1 = Column(Float, nullable=True)
    q2 = Column(Float, nullable=True)
    q3 = Column(Float, nullable=True)

    status = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("year", "round", "session", "driver", name="uix_weekend_session_driver"),
        Index("idx_weekend", "year", "round", "session"),
    )