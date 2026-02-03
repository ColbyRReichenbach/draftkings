"""
Gamalyze neuro-marker score generation.

Generates Gamalyze assessment scores based on player latent factors.
Key innovation: Scores are derived from the same latent factors that drive
betting behavior, ensuring automatic correlation.

Gamalyze neuro-marker components:
1. sensitivity_to_loss (0-100): How strongly player reacts to losses
2. sensitivity_to_reward (0-100): How strongly player reacts to wins
3. risk_tolerance (0-100): Willingness to accept risk
4. decision_consistency (0-100): Ability to make consistent decisions

These scores correlate with betting patterns:
- sensitivity_to_loss ↔ bet_escalation_ratio: r=0.72
- risk_tolerance ↔ market_tier_drift: r=0.58
- decision_consistency ↔ temporal_risk: r=-0.45
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict
from .config import (
    GAMALYZE_MIN,
    GAMALYZE_MAX,
    GAMALYZE_NOISE_STD,
    GAMALYZE_VERSION,
    GAMALYZE_ASSESSMENT_LOOKBACK_DAYS,
    START_DATE,
    RANDOM_SEED
)
from .correlations import add_noise
from .utils import (
    clip_to_valid_range,
    normalize_to_0_100,
    random_date_past_n_days,
    format_date,
    generate_assessment_id
)


def transform_latent_to_gamalyze(latent_sensitivity: np.ndarray,
                                 latent_risk_tolerance: np.ndarray,
                                 latent_consistency: np.ndarray,
                                 noise_std: float = GAMALYZE_NOISE_STD) -> Dict[str, np.ndarray]:
    """
    Transform player latent factors to Gamalyze scores.

    Adds small noise (5% std) to simulate assessment variability while
    maintaining strong correlation with latent factors (r≈0.95).

    Args:
        latent_sensitivity: Raw sensitivity values
        latent_risk_tolerance: Raw risk tolerance values
        latent_consistency: Raw decision consistency values
        noise_std: Standard deviation of noise to add

    Returns:
        Dict with Gamalyze score arrays:
        - sensitivity_to_loss (0-100)
        - sensitivity_to_reward (0-100)
        - risk_tolerance (0-100)
        - decision_consistency (0-100)

    Example:
        >>> latent_sens = np.array([30, 50, 70])
        >>> latent_risk = np.array([35, 55, 75])
        >>> latent_cons = np.array([70, 50, 35])
        >>> scores = transform_latent_to_gamalyze(latent_sens, latent_risk, latent_cons)
        >>> 0 <= scores['sensitivity_to_loss'].min() <= 100
        True
    """
    n = len(latent_sensitivity)

    # Transform latent factors to Gamalyze scores with noise
    # Use latent values as primary signal (95% correlation)
    # Add small noise for realism (5% variance)

    sensitivity_to_loss = add_noise(latent_sensitivity, noise_std)
    sensitivity_to_loss = clip_to_valid_range(sensitivity_to_loss, GAMALYZE_MIN, GAMALYZE_MAX)

    risk_tolerance = add_noise(latent_risk_tolerance, noise_std)
    risk_tolerance = clip_to_valid_range(risk_tolerance, GAMALYZE_MIN, GAMALYZE_MAX)

    decision_consistency = add_noise(latent_consistency, noise_std)
    decision_consistency = clip_to_valid_range(decision_consistency, GAMALYZE_MIN, GAMALYZE_MAX)

    # Sensitivity to reward has moderate correlation with risk tolerance (0.6)
    # Plus some independent variance (0.4)
    sensitivity_to_reward = (
        0.6 * risk_tolerance +
        0.4 * np.random.uniform(GAMALYZE_MIN, GAMALYZE_MAX, size=n)
    )
    sensitivity_to_reward = clip_to_valid_range(sensitivity_to_reward, GAMALYZE_MIN, GAMALYZE_MAX)

    return {
        'sensitivity_to_loss': sensitivity_to_loss,
        'sensitivity_to_reward': sensitivity_to_reward,
        'risk_tolerance': risk_tolerance,
        'decision_consistency': decision_consistency
    }


def generate_gamalyze_scores(players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate Gamalyze assessment scores for all players.

    Creates one assessment per player (except edge case PLR_0333_NJ who has
    no assessment).

    Args:
        players_df: Players DataFrame with latent factors

    Returns:
        DataFrame with Gamalyze assessments:
        - assessment_id
        - player_id
        - assessment_date
        - sensitivity_to_loss (0-100)
        - sensitivity_to_reward (0-100)
        - risk_tolerance (0-100)
        - decision_consistency (0-100)
        - gamalyze_version

    Example:
        >>> from data_generation.player_generator import generate_players
        >>> players = generate_players(100)
        >>> gamalyze = generate_gamalyze_scores(players)
        >>> gamalyze.shape[0] == len(players)
        True
    """
    print(f"Generating Gamalyze scores for {len(players_df)} players...")

    # Set random seed
    np.random.seed(RANDOM_SEED + 1)  # Offset to avoid same RNG as players

    # Extract latent factors
    latent_sensitivity = players_df['latent_sensitivity'].values
    latent_risk_tolerance = players_df['latent_risk_tolerance'].values
    latent_consistency = players_df['latent_consistency'].values

    # Transform to Gamalyze scores
    gamalyze_scores = transform_latent_to_gamalyze(
        latent_sensitivity,
        latent_risk_tolerance,
        latent_consistency
    )

    # Build DataFrame
    gamalyze_records = []

    for i, row in players_df.iterrows():
        # Generate random assessment date (past 90 days from START_DATE)
        assessment_date = random_date_past_n_days(
            START_DATE,
            GAMALYZE_ASSESSMENT_LOOKBACK_DAYS
        )

        record = {
            'assessment_id': generate_assessment_id(row['player_id']),
            'player_id': row['player_id'],
            'assessment_date': format_date(assessment_date),
            'sensitivity_to_loss': round(gamalyze_scores['sensitivity_to_loss'][i], 2),
            'sensitivity_to_reward': round(gamalyze_scores['sensitivity_to_reward'][i], 2),
            'risk_tolerance': round(gamalyze_scores['risk_tolerance'][i], 2),
            'decision_consistency': round(gamalyze_scores['decision_consistency'][i], 2),
            'gamalyze_version': GAMALYZE_VERSION
        }

        gamalyze_records.append(record)

    gamalyze_df = pd.DataFrame(gamalyze_records)

    print(f"✓ Generated {len(gamalyze_df)} Gamalyze assessments")

    return gamalyze_df


def export_gamalyze_csv(gamalyze_df: pd.DataFrame, output_path: str):
    """
    Export Gamalyze scores to CSV.

    Args:
        gamalyze_df: Gamalyze scores DataFrame
        output_path: Path for output CSV

    Returns:
        None (writes file)
    """
    gamalyze_df.to_csv(output_path, index=False)
    print(f"✓ Exported Gamalyze scores to {output_path}")


# =============================================================================
# VALIDATION
# =============================================================================

def validate_gamalyze_scores(gamalyze_df: pd.DataFrame,
                             players_df: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate Gamalyze score generation.

    Args:
        gamalyze_df: Generated Gamalyze scores
        players_df: Original players DataFrame

    Returns:
        Dict of test_name: passed (bool)
    """
    results = {}

    # Count validation
    expected_count = len(players_df)
    actual_count = len(gamalyze_df)
    results['count_match'] = actual_count == expected_count
    print(f"  Count: {actual_count} (expected: {expected_count}) "
          f"{'✓' if results['count_match'] else '✗'}")

    # Value range validation
    score_columns = ['sensitivity_to_loss', 'sensitivity_to_reward',
                    'risk_tolerance', 'decision_consistency']

    for col in score_columns:
        in_range = ((gamalyze_df[col] >= 0) & (gamalyze_df[col] <= 100)).all()
        results[f'{col}_range'] = in_range
        print(f"  {col} in [0, 100]: {'✓' if in_range else '✗'}")

    # No null values
    results['no_nulls'] = gamalyze_df.notna().all().all()
    print(f"  No null values: {'✓' if results['no_nulls'] else '✗'}")

    # Correlation with latent factors (should be high r≈0.95)
    merged = players_df.merge(gamalyze_df, on='player_id')

    corr_sens = np.corrcoef(
        merged['latent_sensitivity'],
        merged['sensitivity_to_loss']
    )[0, 1]
    results['high_corr_sensitivity'] = corr_sens > 0.90
    print(f"  Latent sensitivity correlation: {corr_sens:.3f} "
          f"(expected >0.90) {'✓' if results['high_corr_sensitivity'] else '✗'}")

    corr_risk = np.corrcoef(
        merged['latent_risk_tolerance'],
        merged['risk_tolerance']
    )[0, 1]
    results['high_corr_risk'] = corr_risk > 0.90
    print(f"  Latent risk tolerance correlation: {corr_risk:.3f} "
          f"(expected >0.90) {'✓' if results['high_corr_risk'] else '✗'}")

    # Score statistics
    mean_sens = gamalyze_df['sensitivity_to_loss'].mean()
    mean_cons = gamalyze_df['decision_consistency'].mean()
    print(f"  Mean sensitivity_to_loss: {mean_sens:.1f}")
    print(f"  Mean decision_consistency: {mean_cons:.1f}")

    return results


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GAMALYZE GENERATOR TEST")
    print("=" * 60)

    # Import player generator
    from .player_generator import generate_players

    # Generate test sample
    print("\n1. Generating players...")
    players = generate_players(1000)

    print("\n2. Generating Gamalyze scores...")
    gamalyze = generate_gamalyze_scores(players)

    print("\n3. Validation:")
    results = validate_gamalyze_scores(gamalyze, players)

    if all(results.values()):
        print("\n✅ All Gamalyze generation tests passed!")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"\n⚠ {len(failed)} tests failed: {failed}")

    print("\n4. Sample Gamalyze scores:")
    print(gamalyze[['player_id', 'sensitivity_to_loss', 'risk_tolerance',
                   'decision_consistency']].head(10))

    # Show correlation with latent bet escalation
    merged = players.merge(gamalyze, on='player_id')
    corr_escalation = np.corrcoef(
        merged['sensitivity_to_loss'],
        merged['target_bet_escalation']
    )[0, 1]
    print(f"\n5. Cross-table correlation check:")
    print(f"   sensitivity_to_loss ↔ bet_escalation_ratio: {corr_escalation:.3f}")
    print(f"   (Target: 0.72, should be close due to shared latent factors)")

    print("=" * 60)
