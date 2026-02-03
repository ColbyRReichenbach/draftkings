"""
Player generation with latent psychological factors.

Generates 10,000 players with:
- Demographics (name, age, email, state)
- Risk cohort assignment (90% low, 8% medium, 1.5% high, 0.5% critical)
- Latent factors (psychological "DNA" that drives behavior)

Latent factors ensure correlations across tables:
- Gamalyze scores derived from latent factors
- Betting behavior driven by same latent factors
- Result: automatic correlation between gamalyze_scores.csv and bets.csv
"""

import pandas as pd
import numpy as np
from faker import Faker
from typing import List, Dict
from .config import (
    TOTAL_PLAYERS,
    COHORT_DISTRIBUTION,
    STATE_DISTRIBUTION,
    BEHAVIOR_RANGES,
    RANDOM_SEED
)
from .correlations import generate_latent_factors_for_cohort
from .utils import generate_player_id


def assign_cohorts(n_players: int) -> np.ndarray:
    """
    Assign risk cohorts to players based on distribution.

    Args:
        n_players: Total number of players

    Returns:
        Array of cohort labels

    Example:
        >>> cohorts = assign_cohorts(10000)
        >>> (cohorts == 'low_risk').sum()
        9000  # 90%
    """
    cohorts = np.random.choice(
        list(COHORT_DISTRIBUTION.keys()),
        size=n_players,
        p=list(COHORT_DISTRIBUTION.values())
    )
    return cohorts


def assign_states(n_players: int) -> np.ndarray:
    """
    Assign states to players based on distribution.

    Args:
        n_players: Total number of players

    Returns:
        Array of state codes (MA, NJ, PA)

    Example:
        >>> states = assign_states(10000)
        >>> (states == 'MA').sum() / len(states)
        0.40  # Approximately 40%
    """
    states = np.random.choice(
        list(STATE_DISTRIBUTION.keys()),
        size=n_players,
        p=list(STATE_DISTRIBUTION.values())
    )
    return states


def generate_latent_factors_all_cohorts(cohort_assignments: np.ndarray) -> np.ndarray:
    """
    Generate latent factors for all players across all cohorts.

    Each cohort has different mean latent factors:
    - Low-risk: Low sensitivity, high consistency
    - Critical: High sensitivity, low consistency

    Args:
        cohort_assignments: Array of cohort labels for each player

    Returns:
        Array of shape (n_players, 4) with latent factors:
        - Column 0: sensitivity_to_loss (raw, 0-100 scale)
        - Column 1: risk_tolerance (raw, 0-100 scale)
        - Column 2: decision_consistency (raw, 0-100 scale)
        - Column 3: bet_escalation_ratio (1.0-5.0 scale)
    """
    n_players = len(cohort_assignments)
    latent_factors = np.zeros((n_players, 4))

    # Generate factors separately for each cohort
    for cohort in COHORT_DISTRIBUTION.keys():
        cohort_mask = (cohort_assignments == cohort)
        n_in_cohort = cohort_mask.sum()

        if n_in_cohort > 0:
            cohort_factors = generate_latent_factors_for_cohort(n_in_cohort, cohort)
            latent_factors[cohort_mask] = cohort_factors

    return latent_factors


def generate_player_demographics(n_players: int,
                                 states: np.ndarray) -> List[Dict]:
    """
    Generate realistic player demographics using Faker.

    Args:
        n_players: Number of players
        states: Array of state assignments

    Returns:
        List of dicts with demographic data
    """
    fake = Faker()
    Faker.seed(RANDOM_SEED)

    demographics = []
    for i in range(n_players):
        player_id = generate_player_id(i, states[i])

        demographics.append({
            'player_id': player_id,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'age': np.random.randint(21, 76),  # Legal age to 75
            'state': states[i]
        })

    return demographics


def generate_players(n_players: int = TOTAL_PLAYERS) -> pd.DataFrame:
    """
    Generate complete player dataset with demographics and latent factors.

    This is the entry point for player generation. Creates a DataFrame with:
    - Public columns: player_id, first_name, last_name, email, age, state, risk_cohort
    - Internal columns: latent_sensitivity, latent_risk_tolerance,
                       latent_consistency, target_bet_escalation

    Internal columns are used by other generators but not exported to CSV.

    Args:
        n_players: Total number of players to generate (default: 10,000)

    Returns:
        DataFrame with player data and latent factors

    Example:
        >>> players = generate_players(100)
        >>> players.shape
        (100, 11)  # 6 public + 4 latent + 1 cohort
        >>> 'latent_sensitivity' in players.columns
        True
    """
    print(f"Generating {n_players} players...")

    # Set random seed for reproducibility
    np.random.seed(RANDOM_SEED)

    # Step 1: Assign cohorts
    cohorts = assign_cohorts(n_players)
    cohort_counts = pd.Series(cohorts).value_counts()
    print(f"  Cohort distribution:")
    for cohort, count in cohort_counts.items():
        pct = 100 * count / n_players
        print(f"    {cohort}: {count} ({pct:.1f}%)")

    # Step 2: Assign states
    states = assign_states(n_players)
    state_counts = pd.Series(states).value_counts()
    print(f"  State distribution:")
    for state, count in state_counts.items():
        pct = 100 * count / n_players
        print(f"    {state}: {count} ({pct:.1f}%)")

    # Step 3: Generate latent factors (the "genetic code")
    print(f"  Generating correlated latent factors...")
    latent_factors = generate_latent_factors_all_cohorts(cohorts)

    # Step 4: Generate demographics
    print(f"  Generating demographics...")
    demographics = generate_player_demographics(n_players, states)

    # Step 5: Combine into DataFrame
    players_df = pd.DataFrame(demographics)

    # Add cohort
    players_df['risk_cohort'] = cohorts

    # Add latent factors (these are internal, not exported)
    players_df['latent_sensitivity'] = latent_factors[:, 0]
    players_df['latent_risk_tolerance'] = latent_factors[:, 1]
    players_df['latent_consistency'] = latent_factors[:, 2]
    players_df['target_bet_escalation'] = latent_factors[:, 3]

    # Clamp escalation targets to cohort-specific ranges for consistent bet escalation behavior
    for cohort, ranges in BEHAVIOR_RANGES.items():
        min_ratio, max_ratio = ranges['bet_escalation_ratio']
        mask = players_df['risk_cohort'] == cohort
        if mask.any():
            players_df.loc[mask, 'target_bet_escalation'] = (
                players_df.loc[mask, 'target_bet_escalation'].clip(min_ratio, max_ratio)
            )

    print(f"✓ Generated {len(players_df)} players")

    return players_df


def get_players_by_cohort(players_df: pd.DataFrame, cohort: str) -> pd.DataFrame:
    """
    Filter players by risk cohort.

    Args:
        players_df: Full players DataFrame
        cohort: Cohort to filter ('low_risk', 'medium_risk', 'high_risk', 'critical')

    Returns:
        Filtered DataFrame

    Example:
        >>> players = generate_players(1000)
        >>> high_risk = get_players_by_cohort(players, 'high_risk')
        >>> len(high_risk) / len(players)
        0.015  # Approximately 1.5%
    """
    return players_df[players_df['risk_cohort'] == cohort].copy()


def get_players_by_state(players_df: pd.DataFrame, state: str) -> pd.DataFrame:
    """
    Filter players by state.

    Args:
        players_df: Full players DataFrame
        state: State code (MA, NJ, PA)

    Returns:
        Filtered DataFrame

    Example:
        >>> players = generate_players(1000)
        >>> ma_players = get_players_by_state(players, 'MA')
        >>> len(ma_players) / len(players)
        0.40  # Approximately 40%
    """
    return players_df[players_df['state'] == state].copy()


def export_players_csv(players_df: pd.DataFrame, output_path: str):
    """
    Export players to CSV (without internal latent columns).

    Removes latent factor columns before export as these are internal only.

    Args:
        players_df: Full players DataFrame
        output_path: Path for output CSV

    Returns:
        None (writes file)
    """
    # Define public columns (exclude latent factors)
    public_columns = [
        'player_id',
        'first_name',
        'last_name',
        'email',
        'age',
        'state',
        'risk_cohort'
    ]

    # Export only public columns
    players_df[public_columns].to_csv(output_path, index=False)
    print(f"✓ Exported players to {output_path}")


# =============================================================================
# VALIDATION
# =============================================================================

def validate_player_generation(players_df: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate player generation meets requirements.

    Args:
        players_df: Generated players DataFrame

    Returns:
        Dict of test_name: passed (bool)
    """
    results = {}

    # Count validation
    results['player_count'] = len(players_df) == TOTAL_PLAYERS
    print(f"  Player count: {len(players_df)} (expected: {TOTAL_PLAYERS}) "
          f"{'✓' if results['player_count'] else '✗'}")

    # Cohort distribution (±1% tolerance)
    cohort_counts = players_df['risk_cohort'].value_counts(normalize=True)
    for cohort, expected_pct in COHORT_DISTRIBUTION.items():
        actual_pct = cohort_counts.get(cohort, 0.0)
        diff = abs(actual_pct - expected_pct)
        passed = diff <= 0.01  # ±1% tolerance
        results[f'cohort_{cohort}'] = passed
        print(f"  {cohort}: {actual_pct:.3f} (expected: {expected_pct:.3f}) "
              f"{'✓' if passed else '✗'}")

    # State distribution (±2% tolerance)
    state_counts = players_df['state'].value_counts(normalize=True)
    for state, expected_pct in STATE_DISTRIBUTION.items():
        actual_pct = state_counts.get(state, 0.0)
        diff = abs(actual_pct - expected_pct)
        passed = diff <= 0.02  # ±2% tolerance
        results[f'state_{state}'] = passed
        print(f"  {state}: {actual_pct:.3f} (expected: {expected_pct:.3f}) "
              f"{'✓' if passed else '✗'}")

    # Data quality checks
    results['no_null_ids'] = players_df['player_id'].notna().all()
    results['valid_ages'] = ((players_df['age'] >= 21) & (players_df['age'] <= 75)).all()
    results['valid_states'] = players_df['state'].isin(['MA', 'NJ', 'PA']).all()
    results['has_latent_factors'] = all(
        col in players_df.columns
        for col in ['latent_sensitivity', 'latent_risk_tolerance',
                   'latent_consistency', 'target_bet_escalation']
    )

    # Print data quality results
    print(f"  No null IDs: {'✓' if results['no_null_ids'] else '✗'}")
    print(f"  Valid ages (21-75): {'✓' if results['valid_ages'] else '✗'}")
    print(f"  Valid states (MA/NJ/PA): {'✓' if results['valid_states'] else '✗'}")
    print(f"  Has latent factors: {'✓' if results['has_latent_factors'] else '✗'}")

    # Latent factor checks
    sensitivity_mean = players_df['latent_sensitivity'].mean()
    escalation_mean = players_df['target_bet_escalation'].mean()
    print(f"  Mean latent sensitivity: {sensitivity_mean:.1f}")
    print(f"  Mean bet escalation ratio: {escalation_mean:.2f}")

    return results


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PLAYER GENERATOR TEST")
    print("=" * 60)

    # Generate test sample
    players = generate_players(1000)

    print("\nValidation:")
    results = validate_player_generation(players)

    if all(results.values()):
        print("\n✅ All player generation tests passed!")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"\n⚠ {len(failed)} tests failed: {failed}")

    print("\nSample players:")
    print(players[['player_id', 'first_name', 'last_name', 'state',
                  'risk_cohort', 'target_bet_escalation']].head(10))

    print("=" * 60)
