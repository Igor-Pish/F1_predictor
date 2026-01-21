from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from .db import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    round = Column(Integer, nullable=False)
    name = Column(String, nullable=False, default="")

    __table_args__ = (
        UniqueConstraint("year", "round", name="uq_events_year_round"),
        Index("ix_events_year_round", "year", "round"),
    )

    sessions = relationship("Session", back_populates="event", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    code = Column(String, nullable=False)       # "R", "Q", "FP1", ...
    source = Column(String, nullable=False)     # "fastf1"

    __table_args__ = (
        UniqueConstraint("event_id", "code", "source", name="uq_sessions_event_code_source"),
        Index("ix_sessions_event_code_source", "event_id", "code", "source"),
    )

    event = relationship("Event", back_populates="sessions")
    results = relationship("SessionResult", back_populates="session", cascade="all, delete-orphan")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)   # "VER"
    name = Column(String, nullable=False, default="")

    __table_args__ = (
        UniqueConstraint("code", name="uq_drivers_code"),
        Index("ix_drivers_code", "code"),
    )


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("name", name="uq_teams_name"),
        Index("ix_teams_name", "name"),
    )


class SessionResult(Base):
    __tablename__ = "session_results"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    position = Column(Integer, nullable=True)
    status = Column(String, nullable=True)

    q1_sec = Column(Float, nullable=True)
    q2_sec = Column(Float, nullable=True)
    q3_sec = Column(Float, nullable=True)

    best_lap_sec = Column(Float, nullable=True)
    laps = Column(Integer, nullable=True)
    main_compound = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("session_id", "driver_id", name="uq_session_results_session_driver"),
        Index("ix_session_results_session", "session_id"),
    )

    session = relationship("Session", back_populates="results")
    driver = relationship("Driver")
    team = relationship("Team")