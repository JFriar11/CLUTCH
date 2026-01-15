import argparse
import os
import pandas as pd

from .config import (
    DEFAULT_START_DATE, DEFAULT_END_DATE,
    MIN_HIGH_LEV_PA, MIN_ALL_PA
)
from .data_pull import pull_statcast_pa
from .features import prepare_pa_frame
from .metrics import woba, ops, k_pct
from .clutch_score import compute_clutch_factor

def ensure_dirs():
    os.makedirs("outputs/leaderboards", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Compute MLB Clutch Factor leaderboard (2025 default).")
    parser.add_argument("--start", default=DEFAULT_START_DATE, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=DEFAULT_END_DATE, help="End date YYYY-MM-DD")
    parser.add_argument("--chunk_days", type=int, default=7, help="Days per Statcast pull chunk")
    parser.add_argument("--min_high_pa", type=int, default=MIN_HIGH_LEV_PA, help="Min high leverage PA")
    parser.add_argument("--min_all_pa", type=int, default=MIN_ALL_PA, help="Min total PA")
    args = parser.parse_args()

    ensure_dirs()

    raw = pull_statcast_pa(args.start, args.end, chunk_days=args.chunk_days)
    df = prepare_pa_frame(raw)

    if df.empty:
        print("No data pulled. Check date range.")
        return

    all_pa = df.copy()
    high_pa = df[df["is_high_lev"]].copy()

    pa_all = all_pa.groupby("batter_name").size()
    pa_high = high_pa.groupby("batter_name").size()

    woba_all = woba(all_pa)
    woba_high = woba(high_pa)

    ops_all = ops(all_pa)
    ops_high = ops(high_pa)

    k_all = k_pct(all_pa)
    k_high = k_pct(high_pa)

    clutch = compute_clutch_factor(woba_all, woba_high, ops_all, ops_high, k_all, k_high)

    out = pd.DataFrame({
        "PA_all": pa_all,
        "PA_high": pa_high,
        "wOBA_all": woba_all,
        "wOBA_high": woba_high,
        "OPS_all": ops_all,
        "OPS_high": ops_high,
        "K%_all": k_all,
        "K%_high": k_high,
        "ClutchFactor": clutch,
        "LI_used_in_flag": df["li_used"].iloc[0] if "li_used" in df.columns and len(df) > 0 else False
    }).fillna(0.0)

    # Sample size filters
    out = out[(out["PA_high"] >= args.min_high_pa) & (out["PA_all"] >= args.min_all_pa)]
    out = out.sort_values("ClutchFactor", ascending=False)

    leaderboard_path = "outputs/leaderboards/clutch_leaderboard_2025.csv"
    out.to_csv(leaderboard_path, index=True)
    print(f"Saved leaderboard -> {leaderboard_path}")

    # Show top/bottom in console
    print("\nTop 15 (most clutch):")
    print(out.head(15)[["PA_high", "wOBA_high", "OPS_high", "K%_high", "ClutchFactor"]])

    print("\nBottom 15 (least clutch):")
    print(out.tail(15)[["PA_high", "wOBA_high", "OPS_high", "K%_high", "ClutchFactor"]])

if __name__ == "__main__":
    main()
