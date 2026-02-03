"""
Central configuration for DK Sentinel data generation.

Contains all constants, distributions, behavioral ranges, and target correlations
used throughout the data generation pipeline.

All values are research-backed from:
- NCPG (National Council on Problem Gambling)
- AGA (American Gaming Association)
- Auer & Griffiths (2022) temporal patterns study
- Mindway AI Gamalyze technical documentation
"""

import numpy as np
from typing import Dict, Tuple

# =============================================================================
# GENERATION PARAMETERS
# =============================================================================

TOTAL_PLAYERS = 10000
TARGET_TOTAL_BETS = 500000  # Approximate (driven by per-cohort bets_per_week, not enforced)
RANDOM_SEED = 42  # For reproducibility

# =============================================================================
# TEMPORAL WINDOW
# =============================================================================

START_DATE = '2026-01-01'
END_DATE = '2026-03-31'  # 90-day window to target ~500k bets
DAYS_IN_WINDOW = 90
WEEKS_IN_WINDOW = 90 / 7  # ~12.9 weeks

# =============================================================================
# PLAYER COHORT DISTRIBUTION
# =============================================================================

# Research-backed prevalence rates (NCPG 2023)
COHORT_DISTRIBUTION: Dict[str, float] = {
    'low_risk': 0.90,      # 9,000 players - recreational patterns
    'medium_risk': 0.08,   # 800 players - occasional loss-chasing
    'high_risk': 0.015,    # 150 players - consistent escalation
    'critical': 0.005      # 50 players - severe problem gambling
}

# Verify distribution sums to 1.0
assert abs(sum(COHORT_DISTRIBUTION.values()) - 1.0) < 0.0001, \
    "Cohort distribution must sum to 1.0"

# =============================================================================
# GEOGRAPHIC DISTRIBUTION
# =============================================================================

# Focus on three states with distinct regulatory frameworks
STATE_DISTRIBUTION: Dict[str, float] = {
    'MA': 0.40,  # 4,000 players - Massachusetts (newest, strictest regulations)
    'NJ': 0.35,  # 3,500 players - New Jersey (most mature market)
    'PA': 0.25   # 2,500 players - Pennsylvania (self-exclusion focus)
}

assert abs(sum(STATE_DISTRIBUTION.values()) - 1.0) < 0.0001, \
    "State distribution must sum to 1.0"

VALID_STATES = ['MA', 'NJ', 'PA']

# =============================================================================
# SPORT DISTRIBUTION (BASELINE FOR LOW-RISK PLAYERS)
# =============================================================================

# Based on AGA (American Gaming Association) 2024 report
SPORT_DISTRIBUTION_BASELINE: Dict[str, float] = {
    'NFL': 0.40,          # 40% - Most popular
    'NBA': 0.25,          # 25%
    'MLB': 0.15,          # 15%
    'NHL': 0.08,          # 8%
    'SOCCER': 0.06,       # 6% - EPL, MLS, La Liga
    'MMA': 0.03,          # 3% - UFC, Boxing
    'TENNIS': 0.02,       # 2%
    'TABLE_TENNIS': 0.01  # 1% - Niche market (desperate betting signal)
}

assert abs(sum(SPORT_DISTRIBUTION_BASELINE.values()) - 1.0) < 0.0001, \
    "Sport distribution must sum to 1.0"

# Market tier classification (1.0 = major sports, 0.2 = niche markets)
MARKET_TIERS: Dict[str, float] = {
    'NFL': 1.0,
    'NBA': 1.0,
    'MLB': 1.0,
    'NHL': 1.0,
    'SOCCER': 0.7,
    'MMA': 0.5,
    'TENNIS': 0.5,
    'TABLE_TENNIS': 0.2
}

# =============================================================================
# BEHAVIORAL PATTERNS BY COHORT
# =============================================================================

# Format: (min, max) tuples for each metric
BEHAVIOR_RANGES: Dict[str, Dict[str, Tuple[float, float]]] = {
    'low_risk': {
        'bet_after_loss_ratio': (0.15, 0.35),      # Low loss-chasing
        'bet_escalation_ratio': (0.9, 1.1),        # Consistent bet sizing
        'bets_per_week': (2, 5),                   # Casual frequency
        'late_night_pct': (0.02, 0.08),           # 2-8% late-night (2-6 AM)
        'market_tier_drift': (-0.1, 0.1),         # Stays in major sports
        'base_bet_amount': (10, 50)               # Small stakes
    },
    'medium_risk': {
        'bet_after_loss_ratio': (0.45, 0.65),      # Moderate loss-chasing
        'bet_escalation_ratio': (1.3, 1.8),        # Some escalation
        'bets_per_week': (10, 20),                 # Higher frequency
        'late_night_pct': (0.15, 0.30),           # 15-30% late-night
        'market_tier_drift': (-0.3, -0.1),        # Some drift to niche
        'base_bet_amount': (25, 100)              # Medium stakes
    },
    'high_risk': {
        'bet_after_loss_ratio': (0.85, 0.95),      # High loss-chasing (tuned)
        'bet_escalation_ratio': (2.5, 4.0),        # Significant escalation (tuned)
        'bets_per_week': (35, 60),                 # High frequency (tuned)
        'late_night_pct': (0.45, 0.60),           # 45-60% late-night (tuned)
        'market_tier_drift': (-0.6, -0.35),       # Clear drift to niche (tuned)
        'base_bet_amount': (50, 250)              # Higher stakes
    },
    'critical': {
        'bet_after_loss_ratio': (0.95, 0.99),      # Nearly always chases (tuned)
        'bet_escalation_ratio': (4.0, 7.0),        # Severe escalation (tuned)
        'bets_per_week': (60, 90),                 # Very high frequency (tuned)
        'late_night_pct': (0.60, 0.75),           # 60-75% late-night (tuned)
        'market_tier_drift': (-0.85, -0.60),      # Extreme drift (desperation, tuned)
        'base_bet_amount': (100, 500)             # High stakes
    }
}

# =============================================================================
# TARGET CORRELATIONS (FOR VALIDATION)
# =============================================================================

# These correlations must be achieved (tolerance ±0.05)
TARGET_CORRELATIONS: Dict[Tuple[str, str], float] = {
    ('sensitivity_to_loss', 'bet_escalation_ratio'): 0.72,    # Strong correlation
    ('risk_tolerance', 'market_tier_drift'): 0.58,            # Moderate correlation
    ('decision_consistency', 'temporal_risk'): -0.45          # Inverse correlation
}

# =============================================================================
# CORRELATION MATRIX FOR LATENT FACTORS
# =============================================================================

# 4x4 correlation matrix for multivariate normal generation
# Order: [sensitivity_to_loss, risk_tolerance, decision_consistency, bet_escalation_ratio]
CORRELATION_MATRIX = np.array([
    #  sens   risk   cons   esc
    [1.00,  0.30, -0.20, 0.72],  # sensitivity_to_loss
    [0.30,  1.00, -0.15, 0.58],  # risk_tolerance
    [-0.20, -0.15, 1.00, -0.45], # decision_consistency (inverse)
    [0.72,  0.58, -0.45, 1.00]   # bet_escalation_ratio
])

# Verify matrix is symmetric
assert np.allclose(CORRELATION_MATRIX, CORRELATION_MATRIX.T), \
    "Correlation matrix must be symmetric"

# Verify diagonal is all 1.0
assert np.allclose(np.diag(CORRELATION_MATRIX), 1.0), \
    "Correlation matrix diagonal must be 1.0"

# =============================================================================
# LATENT FACTOR PARAMETERS BY COHORT
# =============================================================================

# Means for [sensitivity_to_loss, risk_tolerance, decision_consistency, bet_escalation_ratio]
LATENT_FACTOR_MEANS: Dict[str, np.ndarray] = {
    'low_risk': np.array([30, 35, 70, 1.0]),      # Low sensitivity, high consistency
    'medium_risk': np.array([50, 55, 50, 1.5]),   # Moderate values
    'high_risk': np.array([70, 75, 35, 2.5]),     # High sensitivity, low consistency
    'critical': np.array([85, 90, 20, 4.0])       # Extreme values
}

# Standard deviations (same across all cohorts)
LATENT_FACTOR_STDS = np.array([15, 12, 10, 0.5])

# =============================================================================
# GAMALYZE SCORE PARAMETERS
# =============================================================================

# Gamalyze scores are 0-100 scale
GAMALYZE_MIN = 0
GAMALYZE_MAX = 100

# Noise factor for adding variability to latent factors (5% noise)
GAMALYZE_NOISE_STD = 0.05

# Gamalyze version (for metadata)
GAMALYZE_VERSION = "v3.2.1"

# Assessment date range (random date in past 90 days from START_DATE)
GAMALYZE_ASSESSMENT_LOOKBACK_DAYS = 90

# =============================================================================
# BET GENERATION PARAMETERS
# =============================================================================

# Outcome probabilities
WIN_RATE_BASELINE = 0.47  # Reference win rate for recreational betting (slightly below 50% due to vig)

# Cohort-specific win rates to reflect riskier bet selection for high/critical players
# (Lower win rates increase loss-chasing ratios without changing business logic thresholds)
COHORT_WIN_RATES: Dict[str, float] = {
    'low_risk': 0.47,     # Recreational baseline
    'medium_risk': 0.45,  # Slightly riskier selection
    'high_risk': 0.35,    # Longshot/volatile betting
    'critical': 0.30      # Extreme risk-taking (parlays/low-odds hits)
}

# Temporal patterns (hours of day)
PRIMETIME_START_HOUR = 18  # 6 PM
PRIMETIME_END_HOUR = 23    # 11 PM
LATE_NIGHT_START_HOUR = 2  # 2 AM
LATE_NIGHT_END_HOUR = 6    # 6 AM

# Primetime betting distribution (normal distribution parameters)
PRIMETIME_MEAN_HOUR = 20  # 8 PM
PRIMETIME_STD_HOURS = 3   # Standard deviation

# Bet escalation cap (maximum multiplier)
MAX_BET_ESCALATION_MULTIPLIER = 5.0

# Odds format (American odds, e.g., -110, +150)
TYPICAL_ODDS_RANGE = (-200, 300)  # Min/max American odds

# =============================================================================
# EDGE CASE PLAYER IDS
# =============================================================================

# Predefined player IDs for edge cases (replace first 10 players)
EDGE_CASE_PLAYERS = {
    'PLR_0001_MA': '100_percent_win',
    'PLR_0002_NJ': '100_percent_loss',
    'PLR_0003_PA': 'single_bet',
    'PLR_0042_MA': 'table_tennis_only',
    'PLR_0099_NJ': '3am_only',
    'PLR_0156_MA': 'penny_bettor',
    'PLR_0203_PA': 'whale',
    'PLR_0333_NJ': 'no_gamalyze',
    'PLR_0405_MA': 'null_sport',
    'PLR_0500_PA': 'self_exclusion_reversal'
}

# Number of edge cases
NUM_EDGE_CASES = len(EDGE_CASE_PLAYERS)

# =============================================================================
# VALIDATION THRESHOLDS
# =============================================================================

# Count validations
EXPECTED_PLAYERS = TOTAL_PLAYERS
MIN_BETS = 450000  # Allow variance around ~500K target
MAX_BETS = 520000
EXPECTED_GAMALYZE_SCORES = TOTAL_PLAYERS  # Edge case removal not yet implemented

# Statistical test thresholds
CHI_SQUARE_P_THRESHOLD = 0.05  # p > 0.05 means distribution matches
KS_TEST_P_THRESHOLD = 0.05     # p > 0.05 means normal distribution
CORRELATION_TOLERANCE = 0.05   # ±0.05 tolerance on target correlations

# Cohort distribution tolerance (±1%)
COHORT_DISTRIBUTION_TOLERANCE = 0.01

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_cohort_params(cohort: str) -> Dict[str, any]:
    """
    Get all parameters for a given cohort.

    Args:
        cohort: One of 'low_risk', 'medium_risk', 'high_risk', 'critical'

    Returns:
        Dictionary with behavioral ranges, latent factor means/stds
    """
    if cohort not in BEHAVIOR_RANGES:
        raise ValueError(f"Invalid cohort: {cohort}. Must be one of {list(BEHAVIOR_RANGES.keys())}")

    return {
        'behaviors': BEHAVIOR_RANGES[cohort],
        'latent_means': LATENT_FACTOR_MEANS[cohort],
        'latent_stds': LATENT_FACTOR_STDS
    }


def get_niche_sport_boost(cohort: str) -> float:
    """
    Get the niche sport boost percentage for market drift.

    Medium/High/Critical players shift +10/20/30% toward niche markets.

    Args:
        cohort: Player risk cohort

    Returns:
        Percentage boost to niche sports (0.0 to 0.30)
    """
    boosts = {
        'low_risk': 0.0,
        'medium_risk': 0.10,
        'high_risk': 0.20,
        'critical': 0.30
    }
    return boosts.get(cohort, 0.0)


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

def validate_config():
    """Validate configuration consistency."""
    # Verify cohort means match correlation matrix dimensions
    for cohort, means in LATENT_FACTOR_MEANS.items():
        assert len(means) == CORRELATION_MATRIX.shape[0], \
            f"Latent factor means for {cohort} must match correlation matrix dimensions"

    # Verify standard deviations match dimensions
    assert len(LATENT_FACTOR_STDS) == CORRELATION_MATRIX.shape[0], \
        "Latent factor stds must match correlation matrix dimensions"

    # Verify all states are valid
    for state in STATE_DISTRIBUTION.keys():
        assert state in VALID_STATES, f"Invalid state: {state}"

    # Verify all sports have market tiers
    for sport in SPORT_DISTRIBUTION_BASELINE.keys():
        assert sport in MARKET_TIERS, f"Sport {sport} missing from MARKET_TIERS"

    print("✓ Configuration validation passed")


# Run validation on import
if __name__ == "__main__":
    validate_config()
