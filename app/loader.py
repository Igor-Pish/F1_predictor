import fastf1
import os
from fastf1.core import Laps
from sqlalchemy.exc import IntegrityError
from app.db import SessionLocal
from app.models import SessionMetric
from app.utils import safe_total_seconds, most_frequent, safe_int, safe_str, is_na

# кэш как раньше
cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "f1_cache"))
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

def load_session_to_db(year: int, round_num: int, session_code: str) -> int:
    sess = fastf1.get_session(year, round_num, session_code)
    sess.load()

    db = SessionLocal()
    inserted = 0

    results = sess.results
    try:
        laps: Laps = sess.laps
    except Exception:
        laps = None

    by_driver = {}
    if laps is not None and not laps.empty:
        for drv, drv_laps in laps.groupby("Driver"):
            best_lap_sec = safe_total_seconds(drv_laps["LapTime"].min())
            total_laps = int(drv_laps.shape[0])
            compound = most_frequent(drv_laps["Compound"]) if "Compound" in drv_laps.columns else None
            by_driver[str(drv)] = (best_lap_sec, total_laps, compound)

    for _, row in results.iterrows():
        drv = row.get("Abbreviation") or row.get("Driver") or row.get("DriverNumber")
        drv = safe_str(drv)
        team = safe_str(row.get("TeamName"))
        pos  = safe_int(row.get("Position"))

        best_lap, total_laps, compound = (None, None, None)
        if drv in by_driver:
            best_lap, total_laps, compound = by_driver[drv]

        q1 = safe_total_seconds(row.get("Q1"))
        q2 = safe_total_seconds(row.get("Q2"))
        q3 = safe_total_seconds(row.get("Q3"))
        st = row.get("Status") if "Status" in results.columns else None
        st = safe_str(st)

        rec = SessionMetric(
            year=year,
            round=round_num,
            session=session_code,
            driver=drv,
            team=team,
            best_lap=best_lap,
            laps=total_laps,
            main_compound=compound,
            position=pos,
            q1=q1,
            q2=q2,
            q3=q3,
            status=st
        )

        try:
            db.add(rec)
            db.flush()
            inserted += 1
        except IntegrityError:
            db.rollback()
            db.merge(rec)
            inserted += 1  # считаем upsert как «записано»
        except Exception as e:
            db.rollback()
            # можно логировать подробнее, но не валим всю сессию:
            print(f"[load_session_to_db] skip {year}/{round_num} {session_code} {drv}: {e}")

    db.commit()
    db.close()
    return inserted