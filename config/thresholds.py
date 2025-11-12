# backend/config/thresholds.py
import os
from datetime import timedelta


# Toggle features
AUTO_TUNE_ENABLED = os.getenv('AUTO_TUNE_ENABLED', 'true').lower() == 'true'
RISK_DECAY_ENABLED = os.getenv('RISK_DECAY_ENABLED', 'true').lower() == 'true'


# Lookback window for tuning (hours)
TUNE_LOOKBACK_HRS = int(os.getenv('TUNE_LOOKBACK_HRS', '24'))


# MAD multipliers (median + k * MAD)
MAD_K_WARN = float(os.getenv('MAD_K_WARN', '3.0'))
MAD_K_CRIT = float(os.getenv('MAD_K_CRIT', '6.0'))


# Percentile fallback (if MAD uninformative)
PCTL_WARN = float(os.getenv('PCTL_WARN', '0.90'))
PCTL_CRIT = float(os.getenv('PCTL_CRIT', '0.97'))


# Minimum samples to compute tuning
MIN_SAMPLES = int(os.getenv('MIN_SAMPLES', '50'))


# Risk decay parameters
# Half-life in minutes -> lambda for exponential decay: exp(-ln(2) * dt/half_life)
DECAY_HALFLIFE_MIN = float(os.getenv('DECAY_HALFLIFE_MIN', '60'))


# Risk bump sizes
RISK_BUMP_WARN = float(os.getenv('RISK_BUMP_WARN', '5'))
RISK_BUMP_CRIT = float(os.getenv('RISK_BUMP_CRIT', '12'))


# Risk closure thresholds
RISK_CLOSE_THRESHOLD = float(os.getenv('RISK_CLOSE_THRESHOLD', '1.0'))
RISK_COOLDOWN_THRESHOLD = float(os.getenv('RISK_COOLDOWN_THRESHOLD', '3.0'))


# Which metrics to auto‑tune by default
DEFAULT_METRICS = [
'api_latency_ms',
'api_error_rate_pct',
'worker_queue_backlog',
'cpu_pct',
'mem_pct'
]


# Clamp fallbacks if no row exists in risk_policies for metric
FALLBACK_CLAMPS = {
'api_latency_ms': dict(lower_floor=50, upper_cap=2000, min_warn=80, max_warn=1500, min_crit=120, max_crit=2500),
'api_error_rate_pct': dict(lower_floor=0.5, upper_cap=80, min_warn=1.0, max_warn=40, min_crit=2.0, max_crit=60),
'worker_queue_backlog': dict(lower_floor=5, upper_cap=100000, min_warn=10, max_warn=50000, min_crit=20, max_crit=80000),
'cpu_pct': dict(lower_floor=20, upper_cap=100, min_warn=40, max_warn=95, min_crit=60, max_crit=100),
'mem_pct': dict(lower_floor=30, upper_cap=100, min_warn=50, max_warn=97, min_crit=70, max_crit=100),
}