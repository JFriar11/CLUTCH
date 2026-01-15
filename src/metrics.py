import pandas as pd
import numpy as np

def woba(df: pd.DataFrame) -> pd.Series:
    """
    wOBA computed from Statcast woba_value / woba_denom at the player level.
    """
    grp = df.groupby("batter_name", dropna=False)
    num = grp["woba_value"].sum(min_count=1)
    den = grp["woba_denom"].sum(min_count=1).replace(0, np.nan)
    return (num / den).fillna(0.0)

def k_pct(df: pd.DataFrame) -> pd.Series:
    """
    K% = strikeouts / plate appearances.
    """
    grp = df.groupby("batter_name", dropna=False)
    pa = grp.size()
    k = grp.apply(lambda g: (g["events"] == "strikeout").sum())
    return (k / pa).fillna(0.0)

def ops(df: pd.DataFrame) -> pd.Series:
    """
    OPS = OBP + SLG (MVP approximation using Statcast events).
    Notes:
      - OBP ignores sacrifice flies unless present as "sac_fly" events.
      - This is fine for clutch-vs-all deltas and consistent across splits.
    """
    grp = df.groupby("batter_name", dropna=False)

    def _count(g, ev_list):
        return g["events"].isin(ev_list).sum()

    H = grp.apply(lambda g: _count(g, ["single", "double", "triple", "home_run"]))
    BB = grp.apply(lambda g: _count(g, ["walk", "intent_walk"]))
    HBP = grp.apply(lambda g: _count(g, ["hit_by_pitch"]))

    # AB approximation: exclude BB/HBP and obvious non-AB events
    AB = grp.apply(
        lambda g: (~g["events"].isin(["walk","intent_walk","hit_by_pitch","sac_fly","sac_bunt","catcher_interf"])).sum()
    )

    TB = grp.apply(lambda g:
        _count(g, ["single"])*1 +
        _count(g, ["double"])*2 +
        _count(g, ["triple"])*3 +
        _count(g, ["home_run"])*4
    )

    denom_obp = (AB + BB + HBP).replace(0, np.nan)
    obp = (H + BB + HBP) / denom_obp

    denom_slg = AB.replace(0, np.nan)
    slg = TB / denom_slg

    return (obp + slg).fillna(0.0)
