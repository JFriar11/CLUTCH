import pandas as pd
import numpy as np
from .config import WEIGHTS

def zscore(s: pd.Series) -> pd.Series:
    s = s.astype(float)
    sd = s.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return s * 0.0
    return (s - s.mean()) / sd

def compute_clutch_factor(
    woba_all: pd.Series, woba_high: pd.Series,
    ops_all: pd.Series, ops_high: pd.Series,
    k_all: pd.Series, k_high: pd.Series
) -> pd.Series:
    """
    Composite clutch factor using weighted z-scores of deltas:
      Δmetric = metric_high - metric_all

    K% is inverted by using z(-ΔK%)
    """
    d_woba = (woba_high - woba_all).fillna(0.0)
    d_ops  = (ops_high  - ops_all ).fillna(0.0)
    d_k    = (k_high    - k_all   ).fillna(0.0)

    z_woba = zscore(d_woba)
    z_ops  = zscore(d_ops)
    z_k_good = zscore(-d_k)

    clutch = (
        WEIGHTS["woba"] * z_woba +
        WEIGHTS["ops"]  * z_ops +
        WEIGHTS["k_pct"] * z_k_good
    )
    return clutch
