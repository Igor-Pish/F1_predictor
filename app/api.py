from __future__ import annotations

from datetime import datetime
from flask import Blueprint, request, jsonify

import fastf1
from redis import Redis
from rq import Queue
from rq.job import Job

from .db import SessionLocal
from .models import Event, Session, SessionResult, Driver, Team
from .jobs import load_session_job

api = Blueprint("api", __name__, url_prefix="/api")


def _redis_conn() -> Redis:
    # Минимально: дефолт на localhost
    # Можно переопределить через REDIS_URL
    import os
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(url)


def _queue() -> Queue:
    return Queue("default", connection=_redis_conn())


@api.get("/years")
def years():
    # 2002..текущий год (по времени системы)
    current_year = datetime.now().year
    start_year = 2002
    return jsonify(list(range(start_year, current_year + 1)))


@api.get("/rounds")
def rounds():
    year = request.args.get("year", type=int)
    if not year:
        return jsonify({"error": "year is required"}), 400

    schedule = fastf1.get_event_schedule(year)
    out = []
    # Schedule — pandas DF; колонки могут отличаться, берём по типовым
    for _, row in schedule.iterrows():
        rnd = int(row.get("RoundNumber"))
        name = str(row.get("EventName", "") or row.get("OfficialEventName", "") or f"Round {rnd}")
        out.append({"round": rnd, "name": name})
    return jsonify(out)


def _resolve_event_and_session(db, year: int, rnd: int, session_code: str):
    ev = db.query(Event).filter(Event.year == year, Event.round == rnd).one_or_none()
    if not ev:
        return None, None
    s = (
        db.query(Session)
        .filter(Session.event_id == ev.id, Session.code == session_code, Session.source == "fastf1")
        .one_or_none()
    )
    return ev, s


@api.get("/session")
def get_session():
    year = request.args.get("year", type=int)
    rnd = request.args.get("round", type=int)
    session_code = request.args.get("session", type=str)

    if not year or not rnd or not session_code:
        return jsonify({"error": "year, round, session are required"}), 400

    db = SessionLocal()
    try:
        _, s = _resolve_event_and_session(db, year, rnd, session_code)
        if not s:
            return jsonify([])

        # join driver/team for UI-friendly response
        rows = (
            db.query(SessionResult, Driver, Team)
            .join(Driver, Driver.id == SessionResult.driver_id)
            .outerjoin(Team, Team.id == SessionResult.team_id)
            .filter(SessionResult.session_id == s.id)
            .order_by(SessionResult.position.is_(None), SessionResult.position.asc())
            .all()
        )

        out = []
        for res, drv, team in rows:
            out.append(
                {
                    "position": res.position,
                    "driver": drv.code,
                    "team": team.name if team else "",
                    "status": res.status,
                    "q1": res.q1_sec,
                    "q2": res.q2_sec,
                    "q3": res.q3_sec,
                    "best_lap": res.best_lap_sec,
                    "laps": res.laps,
                    "main_compound": res.main_compound,
                }
            )
        return jsonify(out)

    finally:
        db.close()


@api.post("/load-session")
def enqueue_load_session():
    payload = request.get_json(silent=True) or {}
    year = payload.get("year")
    rnd = payload.get("round")
    session_code = payload.get("session")

    if not isinstance(year, int) or not isinstance(rnd, int) or not isinstance(session_code, str):
        return jsonify({"error": "Expected JSON {year:int, round:int, session:str}"}), 400

    q = _queue()
    job = q.enqueue(load_session_job, year, rnd, session_code)

    return jsonify({"job_id": job.id})


@api.get("/jobs/<job_id>")
def job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=_redis_conn())
    except Exception:
        return jsonify({"error": "job not found"}), 404

    status = job.get_status()  # queued/started/finished/failed
    resp = {"job_id": job.id, "status": status}

    if job.is_finished:
        resp["result"] = job.result
    if job.is_failed:
        # job.exc_info содержит traceback строкой
        resp["error"] = job.exc_info

    return jsonify(resp)