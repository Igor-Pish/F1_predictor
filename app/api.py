from flask import Blueprint, request, jsonify
import fastf1
import traceback
from app.db import SessionLocal
from app.models import SessionMetric
from app.loader import load_session_to_db
from app.utils import seconds_to_lapstr

api = Blueprint("api", __name__, url_prefix="/api")

def years_list():
    # можно динамически, но пока фикс: 2003..2025
    return list(range(2003, 2026))

@api.get("/years")
def get_years():
    return jsonify(years_list())

@api.get("/rounds")
def get_rounds():
    year = request.args.get("year", type=int)
    if not year:
        return jsonify({"error": "year is required"}), 400
    try:
        cal = fastf1.get_event_schedule(year)
        rounds = []
        for _, r in cal.iterrows():
            rounds.append({
                "round": int(r["RoundNumber"]),
                "name": str(r["EventName"]),
                "country": str(r["Country"])
            })
        return jsonify(rounds)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.post("/load-session")
def api_load_session():
    data = request.get_json(force=True) or {}
    year = data.get("year")
    rnd = data.get("round")
    session_code = data.get("session")
    if not (year and rnd and session_code):
        return jsonify({"error": "year, round, session are required"}), 400
    try:
        n = load_session_to_db(int(year), int(rnd), str(session_code))
        return jsonify({"inserted": n})
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)  # в консоль сервера
        return jsonify({"error": str(e), "traceback": tb}), 500

@api.get("/session")
def api_session():
    year = request.args.get("year", type=int)
    rnd = request.args.get("round", type=int)
    session_code = request.args.get("session", type=str)
    if not (year and rnd and session_code):
        return jsonify({"error": "year, round, session are required"}), 400

    with SessionLocal() as db:
        rows = (db.query(SessionMetric)
                  .filter(SessionMetric.year == year,
                          SessionMetric.round == rnd,
                          SessionMetric.session == session_code)
                  .order_by(SessionMetric.position.asc().nullslast(),
                            SessionMetric.best_lap.asc().nullslast())
                  .all())

    payload = []
    for r in rows:
        payload.append({
            "driver": r.driver,
            "team": r.team or "—",
            "position": r.position,
            "best_lap": seconds_to_lapstr(r.best_lap),
            "laps": r.laps,
            "compound": r.main_compound or "—",
            "q1": seconds_to_lapstr(r.q1) if session_code in ("Q", "SQ") else None,
            "q2": seconds_to_lapstr(r.q2) if session_code in ("Q", "SQ") else None,
            "q3": seconds_to_lapstr(r.q3) if session_code in ("Q", "SQ") else None,
            "status": r.status if session_code in ("R", "S") else None
        })

    return jsonify(payload)