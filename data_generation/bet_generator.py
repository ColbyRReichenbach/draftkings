"""
Bet generation with loss-chasing state machine.

Generates ~500,000 bets across 10,000 players with realistic patterns:
- Loss-chasing behavior (state machine: NORMAL → CHASING → ESCALATING)
- Temporal patterns (late-night betting increases when chasing)
- Market drift (NFL → Table Tennis for high-risk players)
- Realistic win rates (~47%)

This is the most complex module in the data generation pipeline.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from .config import (
    START_DATE,
    END_DATE,
    WEEKS_IN_WINDOW,
    SPORT_DISTRIBUTION_BASELINE,
    MARKET_TIERS,
    BEHAVIOR_RANGES,
    WIN_RATE_BASELINE,
    COHORT_WIN_RATES,
    PRIMETIME_MEAN_HOUR,
    PRIMETIME_STD_HOURS,
    LATE_NIGHT_START_HOUR,
    LATE_NIGHT_END_HOUR,
    MAX_BET_ESCALATION_MULTIPLIER,
    RANDOM_SEED
)
from .utils import (
    generate_bet_id,
    format_timestamp,
    generate_realistic_odds,
    round_to_cents,
    sample_from_range
)


# =============================================================================
# BETTING STATE MACHINE
# =============================================================================

class BettingStateMachine:
    """
    Finite state machine for realistic loss-chasing behavior.

    States:
    - NORMAL: Regular betting pattern
    - CHASING: After a loss, increased bet size
    - ESCALATING: Multiple consecutive losses, exponential growth

    Transitions:
    - NORMAL --[loss + probability check]--> CHASING
    - CHASING --[loss]--> ESCALATING
    - {CHASING, ESCALATING} --[win]--> NORMAL

    Attributes:
        base_amount: Base bet amount
        target_escalation: Target escalation ratio from latent factors
        chase_probability: Probability of chasing after loss
        late_night_baseline: Baseline late-night betting %
        state: Current state ('NORMAL', 'CHASING', 'ESCALATING')
        consecutive_losses: Count of consecutive losses
        current_late_night_pct: Current late-night betting percentage
    """

    def __init__(self,
                 base_bet_amount: float,
                 target_escalation_ratio: float,
                 bet_after_loss_ratio: float,
                 late_night_pct: float):
        """
        Initialize betting state machine.

        Args:
            base_bet_amount: Base bet amount for normal betting
            target_escalation_ratio: Target escalation (from latent factors)
            bet_after_loss_ratio: Probability of chasing after loss
            late_night_pct: Baseline late-night betting percentage
        """
        self.base_amount = base_bet_amount
        self.target_escalation = max(0.9, target_escalation_ratio)  # Min 0.9
        self.chase_probability = np.clip(bet_after_loss_ratio, 0.0, 1.0)
        self.late_night_baseline = np.clip(late_night_pct, 0.0, 0.7)

        self.state = 'NORMAL'
        self.consecutive_losses = 0
        self.current_late_night_pct = late_night_pct

    def get_next_bet_amount(self) -> float:
        """
        Get bet amount for next bet based on current state.

        Returns:
            Bet amount (dollars)
        """
        if self.state == 'NORMAL':
            # Normal: small variance around base
            return self.base_amount * np.random.uniform(0.8, 1.2)

        elif self.state == 'CHASING':
            # Chasing: escalated by target ratio
            return self.base_amount * self.target_escalation * np.random.uniform(0.9, 1.1)

        elif self.state == 'ESCALATING':
            # Escalating: exponential growth capped at 5x
            multiplier = min(
                self.target_escalation ** self.consecutive_losses,
                MAX_BET_ESCALATION_MULTIPLIER
            )
            return self.base_amount * multiplier

        else:
            return self.base_amount

    def process_outcome(self, outcome: str):
        """
        Update state machine based on bet outcome.

        Args:
            outcome: 'win' or 'loss'
        """
        if outcome == 'loss':
            self.consecutive_losses += 1

            # Decide if player chases based on their chase_probability
            if np.random.random() < self.chase_probability:
                if self.consecutive_losses == 1:
                    self.state = 'CHASING'
                elif self.consecutive_losses >= 2:
                    self.state = 'ESCALATING'
                    # Increase late-night betting when desperate
                    self.current_late_night_pct = min(
                        self.late_night_baseline * (1 + self.consecutive_losses * 0.5),
                        0.70  # Cap at 70%
                    )
            else:
                # Player doesn't chase this time
                self.state = 'NORMAL'
                self.consecutive_losses = 0

        else:  # win
            # Win resets state
            self.state = 'NORMAL'
            self.consecutive_losses = 0
            self.current_late_night_pct = self.late_night_baseline

    def is_chasing(self) -> bool:
        """Check if currently in a chasing state."""
        return self.state in ['CHASING', 'ESCALATING']


# =============================================================================
# SPORT SELECTION WITH MARKET DRIFT
# =============================================================================

def select_sport_with_drift(cohort: str,
                           progress_pct: float) -> str:
    """
    Select sport with gradual market drift over time.

    High-risk and critical players shift from major sports (NFL) to niche
    markets (Table Tennis) as they get more desperate over time.

    Args:
        cohort: Player risk cohort
        progress_pct: Progress through betting window (0.0 = start, 1.0 = end)

    Returns:
        Sport category

    Example:
        >>> # Early in window, high-risk player bets NFL
        >>> sport = select_sport_with_drift('high_risk', 0.1)
        >>> # Later, shifts toward niche
        >>> sport = select_sport_with_drift('high_risk', 0.9)
    """
    # Start with baseline distribution
    dist = SPORT_DISTRIBUTION_BASELINE.copy()

    # Apply market drift for medium/high/critical players (accelerates late in window)
    if cohort == 'medium_risk':
        drift_factor = progress_pct ** 1.5
        niche_boost = drift_factor * 0.12  # gentle drift
    elif cohort == 'high_risk':
        drift_factor = progress_pct ** 2
        niche_boost = drift_factor * 0.35  # stronger late drift
    elif cohort == 'critical':
        drift_factor = progress_pct ** 2.2
        niche_boost = drift_factor * 0.50  # extreme late drift
    else:
        niche_boost = 0.0

    # Late-window exploration increases sport diversity for high/critical cohorts
    if cohort in ['high_risk', 'critical'] and progress_pct > 0.7:
        exploration_prob = 0.20 if cohort == 'high_risk' else 0.35
        if np.random.random() < exploration_prob:
            return np.random.choice(list(dist.keys()))

    if niche_boost > 0:
        # Shift probability mass from major sports to niche/low-tier markets
        dist['TABLE_TENNIS'] += niche_boost * 0.50
        dist['MMA'] += niche_boost * 0.25
        dist['TENNIS'] += niche_boost * 0.25
        dist['NFL'] -= niche_boost * 0.40
        dist['NBA'] -= niche_boost * 0.30
        dist['MLB'] -= niche_boost * 0.30

        # Ensure no negative probabilities
        dist = {k: max(0, v) for k, v in dist.items()}

        # Re-normalize
        total = sum(dist.values())
        dist = {k: v / total for k, v in dist.items()}

    # Sample from distribution
    sports = list(dist.keys())
    probs = list(dist.values())
    return np.random.choice(sports, p=probs)


# =============================================================================
# TEMPORAL PATTERN GENERATION
# =============================================================================

def generate_bet_timestamp(current_date: datetime,
                          end_date: datetime,
                          late_night_pct: float,
                          is_chasing: bool) -> datetime:
    """
    Generate realistic bet timestamp with temporal patterns.

    Normal players: Peak at 8 PM (primetime)
    Chasing players: Shift toward late night (2-6 AM)

    Args:
        current_date: Current date in sequence
        end_date: End of betting window
        late_night_pct: Percentage of bets that are late-night
        is_chasing: Whether player is currently chasing

    Returns:
        Bet timestamp

    Example:
        >>> start = datetime(2026, 1, 1)
        >>> end = datetime(2026, 1, 30)
        >>> ts = generate_bet_timestamp(start, end, 0.1, False)
        >>> isinstance(ts, datetime)
        True
    """
    # Random day increment (faster when chasing)
    if is_chasing:
        days_increment = np.random.exponential(scale=0.3)  # Faster betting
    else:
        days_increment = np.random.exponential(scale=1.0)  # Normal pace

    new_date = current_date + timedelta(days=days_increment)

    # Don't exceed end date
    if new_date > end_date:
        new_date = end_date

    # Select hour based on late-night percentage
    if np.random.random() < late_night_pct:
        # Late night (2 AM - 6 AM)
        hour = np.random.randint(LATE_NIGHT_START_HOUR, LATE_NIGHT_END_HOUR)
    else:
        # Primetime (peak at 8 PM, normal distribution)
        hour = int(np.random.normal(PRIMETIME_MEAN_HOUR, PRIMETIME_STD_HOURS))
        hour = max(6, min(23, hour))  # Clip to 6 AM - 11 PM

    minute = np.random.randint(0, 60)
    second = np.random.randint(0, 60)

    timestamp = new_date.replace(hour=hour, minute=minute, second=second)
    # Enforce monotonic timestamps while preserving time-of-day distribution
    if timestamp < current_date:
        timestamp = timestamp + timedelta(days=1)
        if timestamp > end_date:
            timestamp = end_date
    return timestamp


# =============================================================================
# BET GENERATION FOR SINGLE PLAYER
# =============================================================================

def generate_bets_for_single_player(player: pd.Series,
                                   bet_id_start: int) -> List[Dict]:
    """
    Generate betting sequence for a single player.

    Uses state machine to simulate realistic loss-chasing patterns.

    Args:
        player: Player row from players DataFrame
        bet_id_start: Starting bet ID number

    Returns:
        List of bet dictionaries

    Example:
        >>> # Assume player is a Series with required fields
        >>> bets = generate_bets_for_single_player(player, 0)
        >>> len(bets) > 0
        True
    """
    cohort = player['risk_cohort']
    behavior = BEHAVIOR_RANGES[cohort]

    # Determine number of bets
    bets_per_week = sample_from_range(behavior['bets_per_week'])
    total_bets = int(bets_per_week * WEEKS_IN_WINDOW)

    # Initialize state machine
    base_bet_amount = sample_from_range(behavior['base_bet_amount'])
    state_machine = BettingStateMachine(
        base_bet_amount=base_bet_amount,
        target_escalation_ratio=player['target_bet_escalation'],
        bet_after_loss_ratio=sample_from_range(behavior['bet_after_loss_ratio']),
        late_night_pct=sample_from_range(behavior['late_night_pct'])
    )

    # Generate bets
    bets = []
    current_date = datetime.strptime(START_DATE, '%Y-%m-%d')
    end = datetime.strptime(END_DATE, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)

    for bet_num in range(total_bets):
        if current_date >= end:
            break
        # Progress through betting window (0.0 to 1.0)
        progress_pct = bet_num / max(total_bets, 1)

        # Generate timestamp
        timestamp = generate_bet_timestamp(
            current_date,
            end,
            state_machine.current_late_night_pct,
            state_machine.is_chasing()
        )

        # Select sport (with market drift)
        sport = select_sport_with_drift(cohort, progress_pct)

        # Get bet amount from state machine
        bet_amount = state_machine.get_next_bet_amount()
        bet_amount = round_to_cents(max(0.01, bet_amount))  # Minimum $0.01

        # Generate realistic odds
        odds = generate_realistic_odds(sport)

        # Simulate outcome (cohort-specific win rates)
        win_rate = COHORT_WIN_RATES.get(cohort, WIN_RATE_BASELINE)
        outcome = 'win' if np.random.random() < win_rate else 'loss'

        # Update state machine
        state_machine.process_outcome(outcome)

        # Create bet record
        bet = {
            'bet_id': generate_bet_id(bet_id_start + bet_num),
            'player_id': player['player_id'],
            'bet_timestamp': format_timestamp(timestamp),
            'sport_category': sport,
            'market_type': 'moneyline',  # Simplified
            'bet_amount': bet_amount,
            'odds_american': odds,
            'outcome': outcome,
            'market_tier': MARKET_TIERS[sport]
        }

        bets.append(bet)

        # Advance current date
        current_date = timestamp

    return bets


# =============================================================================
# BET GENERATION FOR ALL PLAYERS
# =============================================================================

def generate_bets_for_all_players(players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate betting sequences for all players.

    This is the main entry point for bet generation. Generates ~500,000 bets
    across 10,000 players with realistic patterns.

    Args:
        players_df: Players DataFrame with latent factors

    Returns:
        DataFrame with all bets:
        - bet_id
        - player_id
        - bet_timestamp
        - sport_category
        - market_type
        - bet_amount
        - odds_american
        - outcome
        - market_tier

    Example:
        >>> from data_generation.player_generator import generate_players
        >>> players = generate_players(100)
        >>> bets = generate_bets_for_all_players(players)
        >>> len(bets) > 200  # At least 2 bets per player avg
        True
    """
    print(f"Generating bets for {len(players_df)} players...")
    print(f"  (This may take 2-3 minutes for full 10K player dataset)")

    # Set random seed
    np.random.seed(RANDOM_SEED + 2)  # Offset from other generators

    all_bets = []
    bet_counter = 0

    # Generate bets for each player
    for idx, player in players_df.iterrows():
        player_bets = generate_bets_for_single_player(player, bet_counter)
        all_bets.extend(player_bets)
        bet_counter += len(player_bets)

        # Progress indicator every 1000 players
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1}/{len(players_df)} players "
                  f"({len(all_bets)} bets so far)...")

    bets_df = pd.DataFrame(all_bets)

    print(f"✓ Generated {len(bets_df)} total bets")

    # Print bet distribution by cohort
    merged = players_df.merge(bets_df, on='player_id')
    cohort_bet_counts = merged.groupby('risk_cohort').size()
    print(f"\n  Bets by cohort:")
    for cohort, count in cohort_bet_counts.items():
        avg_per_player = count / len(players_df[players_df['risk_cohort'] == cohort])
        print(f"    {cohort}: {count} bets ({avg_per_player:.1f} avg per player)")

    return bets_df


def export_bets_csv(bets_df: pd.DataFrame, output_path: str):
    """
    Export bets to CSV.

    Args:
        bets_df: Bets DataFrame
        output_path: Path for output CSV

    Returns:
        None (writes file)
    """
    # Select columns for export
    export_columns = [
        'bet_id',
        'player_id',
        'bet_timestamp',
        'sport_category',
        'market_type',
        'bet_amount',
        'odds_american',
        'outcome'
    ]

    bets_df[export_columns].to_csv(output_path, index=False)
    print(f"✓ Exported bets to {output_path}")


# =============================================================================
# VALIDATION
# =============================================================================

def validate_bet_generation(bets_df: pd.DataFrame,
                           players_df: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate bet generation meets requirements.

    Args:
        bets_df: Generated bets DataFrame
        players_df: Players DataFrame

    Returns:
        Dict of test_name: passed (bool)
    """
    results = {}

    # Count validation (450K-550K range)
    total_bets = len(bets_df)
    results['bet_count_range'] = 450000 <= total_bets <= 550000
    print(f"  Total bets: {total_bets} (expected: 450K-550K) "
          f"{'✓' if results['bet_count_range'] else '✗'}")

    # All players have bets
    unique_players = bets_df['player_id'].nunique()
    results['all_players_have_bets'] = unique_players == len(players_df)
    print(f"  Unique players with bets: {unique_players} (expected: {len(players_df)}) "
          f"{'✓' if results['all_players_have_bets'] else '✗'}")

    # Valid bet amounts
    results['valid_amounts'] = (bets_df['bet_amount'] > 0).all()
    print(f"  All bet amounts > 0: {'✓' if results['valid_amounts'] else '✗'}")

    # Valid outcomes
    results['valid_outcomes'] = bets_df['outcome'].isin(['win', 'loss']).all()
    print(f"  All outcomes are win/loss: {'✓' if results['valid_outcomes'] else '✗'}")

    # Win rate approximately expected cohort-weighted rate
    win_rate = (bets_df['outcome'] == 'win').mean()
    cohort_dist = players_df['risk_cohort'].value_counts(normalize=True)
    expected_win_rate = sum(
        COHORT_WIN_RATES.get(cohort, WIN_RATE_BASELINE) * pct
        for cohort, pct in cohort_dist.items()
    )
    results['realistic_win_rate'] = (expected_win_rate - 0.07) < win_rate < (expected_win_rate + 0.07)
    print(f"  Win rate: {win_rate:.3f} (expected: ~{expected_win_rate:.3f}) "
          f"{'✓' if results['realistic_win_rate'] else '✗'}")

    # Sport distribution
    sport_dist = bets_df['sport_category'].value_counts(normalize=True)
    print(f"\n  Sport distribution:")
    for sport in ['NFL', 'NBA', 'TABLE_TENNIS']:
        if sport in sport_dist.index:
            print(f"    {sport}: {sport_dist[sport]:.3f}")

    return results


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("BET GENERATOR TEST")
    print("=" * 60)

    # Import player generator
    from .player_generator import generate_players

    # Generate small test sample (100 players for faster testing)
    print("\n1. Generating test players...")
    players = generate_players(100)

    print("\n2. Generating bets...")
    bets = generate_bets_for_all_players(players)

    print("\n3. Validation:")
    # Temporarily adjust expected count for small sample
    results = validate_bet_generation(bets, players)

    print("\n4. Sample bets:")
    print(bets[['player_id', 'bet_timestamp', 'sport_category',
               'bet_amount', 'outcome']].head(15))

    # Test state machine behavior
    print("\n5. State machine test:")
    print("  Testing loss-chasing pattern...")

    test_player = players.iloc[0].copy()
    test_bets = generate_bets_for_single_player(test_player, 0)

    # Find sequences of losses followed by increased bets
    bet_amounts = [b['bet_amount'] for b in test_bets[:20]]
    outcomes = [b['outcome'] for b in test_bets[:20]]

    print(f"  First 20 bets for {test_player['player_id']}:")
    for i in range(min(10, len(test_bets))):
        print(f"    Bet {i+1}: ${bet_amounts[i]:.2f} → {outcomes[i]}")

    print("=" * 60)
