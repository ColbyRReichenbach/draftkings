"""
Edge case player definitions.

Defines 10 special test cases for pipeline robustness testing.
These edge cases will replace the first 10 players in the generated dataset.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
from .config import EDGE_CASE_PLAYERS
from .utils import format_timestamp, generate_bet_id


def create_edge_case_players() -> Dict[str, Dict]:
    """
    Define edge case player configurations.

    Returns:
        Dict mapping player_id to edge case configuration
    """
    edge_cases = {
        'PLR_0001_MA': {
            'type': '100_percent_win',
            'description': 'Player with 100% win rate',
            'first_name': 'Lucky',
            'last_name': 'Winner',
            'email': 'lucky.winner@example.com',
            'age': 35,
            'state': 'MA',
            'risk_cohort': 'low_risk',
            'n_bets': 10,
            'force_outcome': 'win'
        },
        'PLR_0002_NJ': {
            'type': '100_percent_loss',
            'description': 'Player with 100% loss rate',
            'first_name': 'Unlucky',
            'last_name': 'Loser',
            'email': 'unlucky.loser@example.com',
            'age': 42,
            'state': 'NJ',
            'risk_cohort': 'critical',
            'n_bets': 15,
            'force_outcome': 'loss'
        },
        'PLR_0003_PA': {
            'type': 'single_bet',
            'description': 'Player with only 1 bet',
            'first_name': 'One',
            'last_name': 'Timer',
            'email': 'one.timer@example.com',
            'age': 28,
            'state': 'PA',
            'risk_cohort': 'low_risk',
            'n_bets': 1,
            'force_outcome': None
        },
        'PLR_0042_MA': {
            'type': 'table_tennis_only',
            'description': 'Player betting only Table Tennis',
            'first_name': 'Ping',
            'last_name': 'Pong',
            'email': 'ping.pong@example.com',
            'age': 31,
            'state': 'MA',
            'risk_cohort': 'high_risk',
            'n_bets': 20,
            'force_sport': 'TABLE_TENNIS'
        },
        'PLR_0099_NJ': {
            'type': '3am_only',
            'description': 'Player betting only at 3 AM',
            'first_name': 'Night',
            'last_name': 'Owl',
            'email': 'night.owl@example.com',
            'age': 39,
            'state': 'NJ',
            'risk_cohort': 'critical',
            'n_bets': 25,
            'force_hour': 3
        },
        'PLR_0156_MA': {
            'type': 'penny_bettor',
            'description': 'Player with $0.01 bets',
            'first_name': 'Penny',
            'last_name': 'Pincher',
            'email': 'penny.pincher@example.com',
            'age': 65,
            'state': 'MA',
            'risk_cohort': 'low_risk',
            'n_bets': 50,
            'force_amount': 0.01
        },
        'PLR_0203_PA': {
            'type': 'whale',
            'description': 'Player with $10,000 bets',
            'first_name': 'High',
            'last_name': 'Roller',
            'email': 'high.roller@example.com',
            'age': 55,
            'state': 'PA',
            'risk_cohort': 'critical',
            'n_bets': 30,
            'force_amount': 10000.00
        },
        'PLR_0333_NJ': {
            'type': 'no_gamalyze',
            'description': 'Player missing Gamalyze score',
            'first_name': 'Missing',
            'last_name': 'Data',
            'email': 'missing.data@example.com',
            'age': 44,
            'state': 'NJ',
            'risk_cohort': 'medium_risk',
            'n_bets': 12,
            'skip_gamalyze': True
        },
        'PLR_0405_MA': {
            'type': 'null_sport',
            'description': 'Player with NULL sport in some bets',
            'first_name': 'Null',
            'last_name': 'Sport',
            'email': 'null.sport@example.com',
            'age': 37,
            'state': 'MA',
            'risk_cohort': 'low_risk',
            'n_bets': 18,
            'force_null_sport_count': 3
        },
        'PLR_0500_PA': {
            'type': 'self_exclusion',
            'description': 'Player with self-exclusion reversal',
            'first_name': 'Self',
            'last_name': 'Excluded',
            'email': 'self.excluded@example.com',
            'age': 48,
            'state': 'PA',
            'risk_cohort': 'critical',
            'n_bets': 22,
            'self_excluded': True
        }
    }

    return edge_cases


def inject_edge_cases(players_df: pd.DataFrame,
                     bets_df: pd.DataFrame,
                     gamalyze_df: pd.DataFrame) -> tuple:
    """
    Replace first 10 players with edge cases.

    This approach maintains exact 10,000 player count by replacing
    instead of appending.

    Args:
        players_df: Generated players DataFrame
        bets_df: Generated bets DataFrame
        gamalyze_df: Generated Gamalyze scores DataFrame

    Returns:
        Tuple of (modified_players, modified_bets, modified_gamalyze)

    Note:
        This is a placeholder implementation. Full implementation would:
        1. Replace first 10 player rows with edge case definitions
        2. Generate custom bets for edge case players
        3. Remove/modify Gamalyze scores as needed
    """
    print("Injecting edge cases...")
    print("  Note: Edge case injection is simplified in this version.")
    print("  Full implementation would replace first 10 players with:")

    edge_configs = create_edge_case_players()
    for player_id, config in edge_configs.items():
        print(f"    - {player_id}: {config['description']}")

    # For now, just remove PLR_0333_NJ from Gamalyze (most critical edge case)
    gamalyze_modified = gamalyze_df[
        gamalyze_df['player_id'] != 'PLR_0333_NJ'
    ].copy()

    if len(gamalyze_modified) < len(gamalyze_df):
        print(f"✓ Removed PLR_0333_NJ from Gamalyze (edge case: missing assessment)")

    return players_df, bets_df, gamalyze_modified


if __name__ == "__main__":
    print("=" * 60)
    print("EDGE CASE DEFINITIONS")
    print("=" * 60)

    edge_configs = create_edge_case_players()

    print(f"\nTotal edge cases: {len(edge_configs)}\n")

    for player_id, config in edge_configs.items():
        print(f"{player_id}:")
        print(f"  Type: {config['type']}")
        print(f"  Description: {config['description']}")
        print(f"  Name: {config['first_name']} {config['last_name']}")
        print(f"  Cohort: {config['risk_cohort']}")
        print()

    print("=" * 60)
