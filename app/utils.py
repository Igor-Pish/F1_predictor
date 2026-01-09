import math
import pandas as pd

def is_na(x):
    try:
        return pd.isna(x)
    except Exception:
        return x is None

def safe_int(x):
    if is_na(x):
        return None
    try:
        return int(x)
    except Exception:
        return None

def safe_str(x):
    if is_na(x):
        return None
    return str(x)

def seconds_to_lapstr(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    m = int(x // 60)
    s = x - m * 60
    return f"{m}:{s:06.3f}"

def safe_total_seconds(val):
    try:
        if pd.isna(val):
            return None
        return val.total_seconds()
    except Exception:
        return None

def most_frequent(series: pd.Series):
    if series is None or series.empty:
        return None
    vc = series.dropna().value_counts()
    if vc.empty:
        return None
    return str(vc.idxmax())