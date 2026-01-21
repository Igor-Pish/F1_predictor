from __future__ import annotations

from typing import Optional, Dict, Any

import pandas as pd
import fastf1

from .db import SessionLocal
from .models import Event, Session, Driver, Team, SessionResult


def _to_seconds(value: Any) -> Optional[float]:
    """
    FastF1 часто отдаёт pandas Timedelta / NaT для Q1/Q2/Q3 и LapTime.
    Приводим к секундам float.
    """
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    # pandas Timedelta
    try:
        return float(value.total_seconds())
    except Exception:
        pass

    # уже число
    try:
        return float(value)
    except Exception:
        return None


def _get_or_create_event(db, year: int, rnd: int, name: str) -> Event:
    ev = db.query(Event).filter(Event.year == year, Event.round == rnd).one_or_none()
    if ev:
        # имя может поменяться/уточниться — обновим
        if name and ev.name != name:
            ev.name = name
        return ev
    ev = Event(year=year, round=rnd, name=name or "")
    db.add(ev)
    db.flush()
    return ev


def _get_or_create_session(db, event_id: int, code: str, source: str) -> Session:
    s = (
        db.query(Session)
        .filter(Session.event_id == event_id, Session.code == code, Session.source == source)
        .one_or_none()
    )
    if s:
        return s
    s = Session(event_id=event_id, code=code, source=source)
    db.add(s)
    db.flush()
    return s


def _get_or_create_driver(db, code: str, name: str) -> Driver:
    d = db.query(Driver).filter(Driver.code == code).one_or_none()
    if d:
        # обновим имя если появилось
        if name and d.name != name:
            d.name = name
        return d
    d = Driver(code=code, name=name or "")
    db.add(d)
    db.flush()
    return d


def _get_or_create_team(db, name: str) -> Team:
    if not name:
        name = ""
    t = db.query(Team).filter(Team.name == name).one_or_none()
    if t:
        return t
    t = Team(name=name)
    db.add(t)
    db.flush()
    return t


def _upsert_session_result(
    db,
    session_id: int,
    driver_id: int,
    team_id: Optional[int],
    payload: Dict[str, Any],
) -> None:
    r = (
        db.query(SessionResult)
        .filter(SessionResult.session_id == session_id, SessionResult.driver_id == driver_id)
        .one_or_none()
    )
    if r is None:
        r = SessionResult(session_id=session_id, driver_id=driver_id)
        db.add(r)

    r.team_id = team_id
    r.position = payload.get("position")
    r.status = payload.get("status")

    r.q1_sec = payload.get("q1_sec")
    r.q2_sec = payload.get("q2_sec")
    r.q3_sec = payload.get("q3_sec")

    r.best_lap_sec = payload.get("best_lap_sec")
    r.laps = payload.get("laps")
    r.main_compound = payload.get("main_compound")


def load_session_job(year: int, round: int, session_code: str) -> Dict[str, Any]:
    """
    RQ job.
    Загружает сессию из FastF1 и сохраняет результаты в SQLite.

    Возвращает короткий отчёт.
    """
    # Воркер — отдельный процесс. Кэш FastF1 надо включить и тут.
    fastf1.Cache.enable_cache("f1_cache")

    source = "fastf1"

    db = SessionLocal()
    try:
        sess = fastf1.get_session(year, round, session_code)
        sess.load()

        # имя ивента постараемся добыть максимально безопасно
        event_name = ""
        try:
            # sess.event часто pandas Series
            if hasattr(sess, "event") and sess.event is not None:
                event_name = str(getattr(sess.event, "EventName", "") or sess.event.get("EventName", "") or "")
        except Exception:
            event_name = ""

        ev = _get_or_create_event(db, year, round, event_name)
        s = _get_or_create_session(db, ev.id, session_code, source)

        results_df = sess.results
        if results_df is None or len(results_df) == 0:
            db.commit()
            return {"ok": True, "inserted_or_updated": 0, "note": "No results in FastF1 session"}

        # Попробуем подготовить статистику по кругам
        laps_df = None
        try:
            laps_df = sess.laps
        except Exception:
            laps_df = None

        lap_stats = {}
        if laps_df is not None and isinstance(laps_df, pd.DataFrame) and len(laps_df) > 0:
            # FastF1 обычно использует колонку 'Driver' (аббревиатура)
            if "Driver" in laps_df.columns:
                # Лучший круг
                if "LapTime" in laps_df.columns:
                    tmp = laps_df.dropna(subset=["Driver", "LapTime"]).copy()
                    if len(tmp) > 0:
                        tmp["LapTimeSec"] = tmp["LapTime"].apply(_to_seconds)
                        best = tmp.groupby("Driver")["LapTimeSec"].min().to_dict()
                    else:
                        best = {}
                else:
                    best = {}

                # Кол-во кругов
                laps_count = laps_df.dropna(subset=["Driver"]).groupby("Driver").size().to_dict()

                # Основной compound (мода)
                if "Compound" in laps_df.columns:
                    comp = laps_df.dropna(subset=["Driver", "Compound"]).copy()
                    if len(comp) > 0:
                        main_compound = (
                            comp.groupby("Driver")["Compound"]
                            .agg(lambda x: x.value_counts().index[0] if len(x.value_counts()) else None)
                            .to_dict()
                        )
                    else:
                        main_compound = {}
                else:
                    main_compound = {}

                # Соберём в один словарь
                for drv in set(list(best.keys()) + list(laps_count.keys()) + list(main_compound.keys())):
                    lap_stats[drv] = {
                        "best_lap_sec": best.get(drv),
                        "laps": int(laps_count.get(drv)) if drv in laps_count else None,
                        "main_compound": main_compound.get(drv),
                    }

        updated = 0

        # В results_df обычно есть:
        # Abbreviation, FullName, TeamName, Position, Status, Q1, Q2, Q3
        for _, row in results_df.iterrows():
            driver_code = None
            driver_name = ""

            # максимально безопасное извлечение
            for key in ("Abbreviation", "Driver", "DriverId", "BroadcastName", "LastName"):
                if key in results_df.columns:
                    v = row.get(key)
                    if v is not None and str(v).strip():
                        driver_code = str(v).strip()
                        break

            if "FullName" in results_df.columns:
                v = row.get("FullName")
                if v is not None:
                    driver_name = str(v).strip()

            if driver_code is None:
                # без кода не можем связать
                continue

            team_name = ""
            if "TeamName" in results_df.columns:
                v = row.get("TeamName")
                team_name = "" if v is None else str(v).strip()
            elif "Team" in results_df.columns:
                v = row.get("Team")
                team_name = "" if v is None else str(v).strip()

            position = None
            if "Position" in results_df.columns:
                v = row.get("Position")
                try:
                    position = int(v) if v is not None and not pd.isna(v) else None
                except Exception:
                    position = None

            status = None
            if "Status" in results_df.columns:
                v = row.get("Status")
                status = None if v is None else str(v)

            q1 = _to_seconds(row.get("Q1")) if "Q1" in results_df.columns else None
            q2 = _to_seconds(row.get("Q2")) if "Q2" in results_df.columns else None
            q3 = _to_seconds(row.get("Q3")) if "Q3" in results_df.columns else None

            extra = lap_stats.get(driver_code, {})
            payload = {
                "position": position,
                "status": status,
                "q1_sec": q1,
                "q2_sec": q2,
                "q3_sec": q3,
                "best_lap_sec": extra.get("best_lap_sec"),
                "laps": extra.get("laps"),
                "main_compound": extra.get("main_compound"),
            }

            d = _get_or_create_driver(db, driver_code, driver_name)
            t = _get_or_create_team(db, team_name) if team_name != "" else None

            _upsert_session_result(db, s.id, d.id, t.id if t else None, payload)
            updated += 1

        db.commit()
        return {"ok": True, "inserted_or_updated": updated}

    finally:
        db.close()