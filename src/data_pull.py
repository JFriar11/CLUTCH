import pandas as pd
from datetime import datetime, timedelta
from pybaseball import statcast

def _daterange_chunks(start_date: str, end_date: str, chunk_days: int = 7):
    """
    Yield (chunk_start, chunk_end) as YYYY-MM-DD strings, inclusive.
    Chunking helps avoid massive single calls.
    """
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    cur = start
    while cur <= end:
        chunk_start = cur
        chunk_end = min(cur + timedelta(days=chunk_days - 1), end)
        yield chunk_start.date().isoformat(), chunk_end.date().isoformat()
        cur = chunk_end + timedelta(days=1)

def pull_statcast_pa(start_date: str, end_date: str, chunk_days: int = 7) -> pd.DataFrame:
    """
    Pull Statcast pitch/PA-level data in chunks and concatenate.
    WARNING: A full season can be large. Chunking is safer.
    """
    parts = []
    for a, b in _daterange_chunks(start_date, end_date, chunk_days=chunk_days):
        print(f"Pulling Statcast data: {a} to {b} ...")
        df = statcast(start_dt=a, end_dt=b)
        if df is not None and len(df) > 0:
            parts.append(df)
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    return out
