"""
Statistical validation for generated data.

Validates that generated data meets all requirements:
- Count validations
- Distribution tests (chi-square, K-S)
- Correlation validations
- Edge case verification
"""

import pandas as pd
import numpy as np
from scipy.stats import chisquare, ks_2samp
from typing import Dict, Tuple
from .config import (
    TARGET_CORRELATIONS,
    CORRELATION_TOLERANCE,
    CHI_SQUARE_P_THRESHOLD,
    KS_TEST_P_THRESHOLD,
    SPORT_DISTRIBUTION_BASELINE,
    EXPECTED_PLAYERS,
    MIN_BETS,
    MAX_BETS,
    EXPECTED_GAMALYZE_SCORES
)


def calculate_bet_metrics_per_player(bets_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate bet-derived metrics aggregated by player.

    Args:
        bets_df: Bets DataFrame

    Returns:
        DataFrame with player-level metrics:
        - bet_escalation_ratio
        - market_tier_drift
        - temporal_risk
    """
    # Group by player
    player_stats = []

    for player_id, player_bets in bets_df.groupby('player_id'):
        # Sort by timestamp
        player_bets = player_bets.sort_values('bet_timestamp')

        # Calculate bet_after_loss_ratio
        player_bets['prev_outcome'] = player_bets['outcome'].shift(1)
        bets_after_loss = (player_bets['prev_outcome'] == 'loss').sum()
        total_bets = len(player_bets)
        bet_after_loss_ratio = bets_after_loss / max(total_bets - 1, 1)

        # Calculate bet_escalation_ratio
        loss_bets = player_bets[player_bets['prev_outcome'] == 'loss']
        win_bets = player_bets[player_bets['prev_outcome'] == 'win']

        if len(loss_bets) > 0 and len(win_bets) > 0:
            avg_bet_after_loss = loss_bets['bet_amount'].mean()
            avg_bet_after_win = win_bets['bet_amount'].mean()
            bet_escalation_ratio = avg_bet_after_loss / max(avg_bet_after_win, 0.01)
        else:
            bet_escalation_ratio = 1.0

        # Calculate market_tier_drift (average tier)
        market_tier_drift = player_bets['market_tier'].mean() if 'market_tier' in player_bets.columns else 1.0

        # Calculate temporal_risk (percentage late-night)
        player_bets['hour'] = pd.to_datetime(player_bets['bet_timestamp']).dt.hour
        late_night_bets = ((player_bets['hour'] >= 2) & (player_bets['hour'] < 6)).sum()
        temporal_risk = late_night_bets / max(total_bets, 1)

        player_stats.append({
            'player_id': player_id,
            'bet_after_loss_ratio': bet_after_loss_ratio,
            'bet_escalation_ratio': bet_escalation_ratio,
            'market_tier_drift': market_tier_drift,
            'temporal_risk': temporal_risk
        })

    return pd.DataFrame(player_stats)


def validate_correlations(gamalyze_df: pd.DataFrame,
                         bets_df: pd.DataFrame) -> Dict[str, Tuple[float, bool]]:
    """
    Validate target correlations are achieved.

    Args:
        gamalyze_df: Gamalyze scores DataFrame
        bets_df: Bets DataFrame

    Returns:
        Dict mapping correlation name to (actual_r, passed)
    """
    print("\nValidating correlations...")

    # Calculate bet metrics
    bet_metrics = calculate_bet_metrics_per_player(bets_df)

    # Merge with Gamalyze
    merged = gamalyze_df.merge(bet_metrics, on='player_id')

    results = {}

    # Test each target correlation
    for (var1, var2), target_r in TARGET_CORRELATIONS.items():
        if var1 in merged.columns and var2 in merged.columns:
            actual_r = np.corrcoef(merged[var1], merged[var2])[0, 1]
            diff = abs(actual_r - target_r)
            passed = diff <= CORRELATION_TOLERANCE

            results[f"{var1}_vs_{var2}"] = (actual_r, passed)

            icon = "✓" if passed else "✗"
            print(f"  {var1} ↔ {var2}: r={actual_r:.3f} "
                  f"(target: {target_r:.3f}, diff: {diff:.3f}) {icon}")
        else:
            print(f"  ⚠ Missing columns for {var1} ↔ {var2}")

    return results


def validate_sport_distribution(bets_df: pd.DataFrame) -> Tuple[float, bool]:
    """
    Chi-square test for sport distribution.

    Args:
        bets_df: Bets DataFrame

    Returns:
        Tuple of (p_value, passed)
    """
    print("\nValidating sport distribution...")

    observed = bets_df['sport_category'].value_counts()
    expected_counts = {
        sport: prob * len(bets_df)
        for sport, prob in SPORT_DISTRIBUTION_BASELINE.items()
    }

    # Align observed and expected
    sports = list(SPORT_DISTRIBUTION_BASELINE.keys())
    obs_values = [observed.get(sport, 0) for sport in sports]
    exp_values = [expected_counts[sport] for sport in sports]

    # Chi-square test
    chi2_stat, p_value = chisquare(f_obs=obs_values, f_exp=exp_values)

    passed = p_value > CHI_SQUARE_P_THRESHOLD

    icon = "✓" if passed else "✗"
    print(f"  Chi-square: χ²={chi2_stat:.2f}, p={p_value:.4f} "
          f"(threshold: {CHI_SQUARE_P_THRESHOLD}) {icon}")

    return p_value, passed


def validate_gamalyze_normality(gamalyze_df: pd.DataFrame) -> Dict[str, Tuple[float, bool]]:
    """
    Kolmogorov-Smirnov test for Gamalyze score normality.

    Args:
        gamalyze_df: Gamalyze scores DataFrame

    Returns:
        Dict mapping score name to (p_value, passed)
    """
    print("\nValidating Gamalyze score distributions...")

    results = {}
    score_columns = ['sensitivity_to_loss', 'risk_tolerance', 'decision_consistency']

    for col in score_columns:
        # Generate normal sample with same mean/std
        scores = gamalyze_df[col].dropna()
        normal_sample = np.random.normal(
            loc=scores.mean(),
            scale=scores.std(),
            size=len(scores)
        )

        # K-S test
        ks_stat, p_value = ks_2samp(scores, normal_sample)

        passed = p_value > KS_TEST_P_THRESHOLD

        results[col] = (p_value, passed)

        icon = "✓" if passed else "✗"
        print(f"  {col}: KS={ks_stat:.4f}, p={p_value:.4f} {icon}")

    return results


def validate_all(players_df: pd.DataFrame,
                bets_df: pd.DataFrame,
                gamalyze_df: pd.DataFrame) -> Dict[str, bool]:
    """
    Run all validation tests.

    Args:
        players_df: Players DataFrame
        bets_df: Bets DataFrame
        gamalyze_df: Gamalyze scores DataFrame

    Returns:
        Dict of test_name: passed (bool)
    """
    print("=" * 60)
    print("VALIDATION SUITE")
    print("=" * 60)

    results = {}

    # Tier 1: Count validations
    print("\n[Tier 1] Count Validations")
    results['player_count'] = len(players_df) == EXPECTED_PLAYERS
    print(f"  Players: {len(players_df)} (expected: {EXPECTED_PLAYERS}) "
          f"{'✓' if results['player_count'] else '✗'}")

    results['bet_count_range'] = MIN_BETS <= len(bets_df) <= MAX_BETS
    print(f"  Bets: {len(bets_df)} (expected: {MIN_BETS}-{MAX_BETS}) "
          f"{'✓' if results['bet_count_range'] else '✗'}")

    results['gamalyze_count'] = len(gamalyze_df) == EXPECTED_GAMALYZE_SCORES
    print(f"  Gamalyze: {len(gamalyze_df)} (expected: {EXPECTED_GAMALYZE_SCORES}) "
          f"{'✓' if results['gamalyze_count'] else '✗'}")

    # Tier 2: Data quality
    print("\n[Tier 2] Data Quality")
    results['no_null_player_ids'] = players_df['player_id'].notna().all()
    print(f"  No null player IDs: {'✓' if results['no_null_player_ids'] else '✗'}")

    results['valid_states'] = players_df['state'].isin(['MA', 'NJ', 'PA']).all()
    print(f"  Valid states: {'✓' if results['valid_states'] else '✗'}")

    results['positive_bets'] = (bets_df['bet_amount'] > 0).all()
    print(f"  All bet amounts > 0: {'✓' if results['positive_bets'] else '✗'}")

    # Tier 3: Distributions
    print("\n[Tier 3] Distributions")
    sport_p, sport_passed = validate_sport_distribution(bets_df)
    results['sport_distribution'] = sport_passed

    gamalyze_norm = validate_gamalyze_normality(gamalyze_df)
    results['gamalyze_normality'] = all(passed for _, passed in gamalyze_norm.values())

    # Tier 4: Correlations
    print("\n[Tier 4] Correlations")
    corr_results = validate_correlations(gamalyze_df, bets_df)
    for name, (actual_r, passed) in corr_results.items():
        results[f'corr_{name}'] = passed

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"Passed: {passed_count}/{total_count} tests")

    if passed_count == total_count:
        print("✅ ALL VALIDATIONS PASSED!")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"⚠ Failed tests: {', '.join(failed)}")

    print("=" * 60)

    return results


if __name__ == "__main__":
    print("Validation module - run via __main__.py")
