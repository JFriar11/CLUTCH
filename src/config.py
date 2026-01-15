DEFAULT_START_DATE = "2025-03-01"
DEFAULT_END_DATE   = "2025-11-15"

# High leverage definition:
# High leverage if (LI > 1.5) OR (inning >= 7 AND abs(score_diff) <= 2)
LI_THRESHOLD = 1.5
LATE_INNING = 7
CLOSE_RUNS = 2

# Minimum PA to reduce noise
MIN_HIGH_LEV_PA = 50
MIN_ALL_PA = 250

# Composite score weights 
# Want lower K% 
WEIGHTS = {
    "woba": 0.50,
    "ops": 0.35,
    "k_pct": 0.15
}
