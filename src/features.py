import pandas as pd
import numpy as np
from .config import LI_THRESHOLD, LATE_INNING, CLOSE_RUNS

def prepare_pa_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep relevant columns, normalize types, and create:
      - batter_name
      - is_high_lev (based on LI if present, plus late/close rule)
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # FIXED: Properly determine batter name
    # Statcast provides 'batter' (ID) but not always 'batter_name'
    # We need to use pybaseball's playerid_reverse_lookup or similar
    if "batter_name" not in df.columns:
        # Try to get batter names from the batter ID
        if "batter" in df.columns:
            try:
                from pybaseball import playerid_reverse_lookup
                unique_batters = df["batter"].dropna().unique()
                
                # Get player names for all unique batter IDs
                player_lookup = playerid_reverse_lookup(unique_batters, key_type='mlbam')
                
                # Create a mapping dictionary
                name_map = dict(zip(
                    player_lookup['key_mlbam'],
                    player_lookup['name_first'] + ' ' + player_lookup['name_last']
                ))
                
                # Map batter IDs to names
                df["batter_name"] = df["batter"].map(name_map)
                
            except Exception as e:
                print(f"Warning: Could not lookup batter names: {e}")
                # Fallback: use batter ID as string
                df["batter_name"] = "Batter_" + df["batter"].astype(str)
        else:
            df["batter_name"] = "Unknown"

    # Ensure needed columns exist
    needed = ["events", "inning", "bat_score", "fld_score", "woba_value", "woba_denom"]
    for c in needed:
        if c not in df.columns:
            df[c] = np.nan

    # Type conversions
    for c in ["inning", "bat_score", "fld_score", "woba_value", "woba_denom"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Late & close proxy
    score_diff = (df["bat_score"] - df["fld_score"]).abs()
    late_close = (df["inning"] >= LATE_INNING) & (score_diff <= CLOSE_RUNS)

    # Optional LI usage if present
    li_col = None
    for candidate in ["li", "LI", "leverage_index", "Leverage_Index", "lev_index"]:
        if candidate in df.columns:
            li_col = candidate
            break

    if li_col is not None:
        li_vals = pd.to_numeric(df[li_col], errors="coerce")
        high_li = li_vals > LI_THRESHOLD
        df["is_high_lev"] = (high_li | late_close).fillna(False)
        df["li_used"] = True
    else:
        df["is_high_lev"] = late_close.fillna(False)
        df["li_used"] = False

    # Keep only rows with an event label (plate appearance result)
    df["events"] = df["events"].astype("string")
    df = df.dropna(subset=["events"])
    
    # Also drop rows where batter_name is missing
    df = df.dropna(subset=["batter_name"])

    return df