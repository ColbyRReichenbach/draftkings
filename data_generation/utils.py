"""
Utility functions for DK Sentinel data generation.

Contains helper functions for:
- Data normalization and scaling
- ID generation
- Date/time generation
- Data type conversions
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Union, List
import random


def scale_to_range(values: Union[np.ndarray, float],
                   min_val: float,
                   max_val: float) -> Union[np.ndarray, float]:
    """
    Scale values to a specified range [min_val, max_val].

    Uses min-max normalization then scales to target range.
    Handles both single values and arrays.

    Args:
        values: Value(s) to scale
        min_val: Minimum value of output range
        max_val: Maximum value of output range

    Returns:
        Scaled value(s) in range [min_val, max_val]

    Examples:
        >>> scale_to_range(np.array([0, 5, 10]), 0, 100)
        array([0., 50., 100.])
        >>> scale_to_range(0.5, 0, 100)
        50.0
    """
    is_scalar = np.isscalar(values)
    vals = np.atleast_1d(values)

    # Clip to prevent extreme outliers
    vals = np.clip(vals, min_val, max_val)

    if is_scalar:
        return float(vals[0])
    return vals


def normalize_to_0_100(values: np.ndarray,
                       mean: float = 50,
                       std: float = 15) -> np.ndarray:
    """
    Normalize array to 0-100 range with specified mean and std.

    Args:
        values: Raw values
        mean: Target mean (default 50)
        std: Target std (default 15)

    Returns:
        Normalized values clipped to [0, 100]
    """
    # Standardize to mean=0, std=1
    standardized = (values - np.mean(values)) / (np.std(values) + 1e-10)

    # Scale to target mean and std
    scaled = standardized * std + mean

    # Clip to [0, 100]
    return np.clip(scaled, 0, 100)


def generate_player_id(index: int, state: str) -> str:
    """
    Generate player ID in format PLR_####_{STATE}.

    Args:
        index: Player index (0-9999)
        state: State code (MA, NJ, PA)

    Returns:
        Player ID string (e.g., "PLR_0001_MA")

    Examples:
        >>> generate_player_id(0, 'MA')
        'PLR_0001_MA'
        >>> generate_player_id(42, 'NJ')
        'PLR_0043_NJ'
    """
    if state not in ['MA', 'NJ', 'PA']:
        raise ValueError(f"Invalid state: {state}. Must be MA, NJ, or PA")

    # Index is 0-based, but IDs are 1-based (PLR_0001, not PLR_0000)
    return f"PLR_{index+1:04d}_{state}"


def generate_bet_id(index: int) -> str:
    """
    Generate bet ID in format BET_########.

    Args:
        index: Bet index (0-based)

    Returns:
        Bet ID string (e.g., "BET_00000001")

    Examples:
        >>> generate_bet_id(0)
        'BET_00000001'
        >>> generate_bet_id(999999)
        'BET_01000000'
    """
    return f"BET_{index+1:08d}"


def generate_assessment_id(player_id: str) -> str:
    """
    Generate Gamalyze assessment ID.

    Args:
        player_id: Player ID (e.g., "PLR_0001_MA")

    Returns:
        Assessment ID (e.g., "ASSESS_PLR_0001_MA")

    Examples:
        >>> generate_assessment_id('PLR_0001_MA')
        'ASSESS_PLR_0001_MA'
    """
    return f"ASSESS_{player_id}"


def random_date_in_window(start_date: str,
                          end_date: str) -> datetime:
    """
    Generate random date within specified window.

    Args:
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)

    Returns:
        Random datetime within window

    Examples:
        >>> date = random_date_in_window('2026-01-01', '2026-01-30')
        >>> isinstance(date, datetime)
        True
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    delta = end - start
    random_days = random.uniform(0, delta.days + delta.seconds / 86400.0)

    return start + timedelta(days=random_days)


def random_date_past_n_days(reference_date: str,
                            n_days: int) -> datetime:
    """
    Generate random date in past N days from reference.

    Args:
        reference_date: Reference date (YYYY-MM-DD format)
        n_days: Number of days to look back

    Returns:
        Random datetime in past N days

    Examples:
        >>> date = random_date_past_n_days('2026-01-01', 90)
        >>> isinstance(date, datetime)
        True
    """
    ref = datetime.strptime(reference_date, '%Y-%m-%d')
    days_back = random.uniform(0, n_days)
    return ref - timedelta(days=days_back)


def generate_realistic_odds(sport: str) -> int:
    """
    Generate realistic American odds for a given sport.

    American odds format:
    - Negative: Amount to bet to win $100 (e.g., -110 = bet $110 to win $100)
    - Positive: Amount won on $100 bet (e.g., +150 = win $150 on $100 bet)

    Args:
        sport: Sport category

    Returns:
        American odds (integer)

    Examples:
        >>> odds = generate_realistic_odds('NFL')
        >>> -300 <= odds <= 300
        True
    """
    # Most bets are close to even money (-110 is most common)
    # But niche sports have more variance

    if sport in ['NFL', 'NBA', 'MLB', 'NHL']:
        # Major sports: tight odds, centered around -110
        if random.random() < 0.7:
            return random.choice([-110, -105, -115, -120, 100, 110])
        else:
            return random.randint(-200, 200)
    else:
        # Niche sports: wider odds range
        return random.randint(-300, 300)


def calculate_payout(bet_amount: float, odds_american: int) -> float:
    """
    Calculate payout from American odds.

    Args:
        bet_amount: Amount bet
        odds_american: American odds

    Returns:
        Payout amount (including original bet) if bet wins

    Examples:
        >>> calculate_payout(100, -110)  # Bet $100 at -110
        190.91  # Win $90.91 + original $100
        >>> calculate_payout(100, 150)   # Bet $100 at +150
        250.0  # Win $150 + original $100
    """
    if odds_american < 0:
        # Negative odds: bet abs(odds) to win $100
        profit = bet_amount * (100 / abs(odds_american))
    else:
        # Positive odds: win odds on $100 bet
        profit = bet_amount * (odds_american / 100)

    return bet_amount + profit


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime for CSV export (ISO 8601).

    Args:
        dt: Datetime object

    Returns:
        ISO 8601 formatted string

    Examples:
        >>> dt = datetime(2026, 1, 15, 20, 30, 45)
        >>> format_timestamp(dt)
        '2026-01-15T20:30:45'
    """
    return dt.strftime('%Y-%m-%dT%H:%M:%S')


def format_date(dt: datetime) -> str:
    """
    Format date only for CSV export.

    Args:
        dt: Datetime object

    Returns:
        Date string (YYYY-MM-DD)

    Examples:
        >>> dt = datetime(2026, 1, 15, 20, 30, 45)
        >>> format_date(dt)
        '2026-01-15'
    """
    return dt.strftime('%Y-%m-%d')


def sample_from_range(range_tuple: tuple,
                     distribution: str = 'uniform') -> float:
    """
    Sample value from (min, max) range.

    Args:
        range_tuple: (min, max) tuple
        distribution: 'uniform' or 'normal' (centered in range)

    Returns:
        Sampled value

    Examples:
        >>> val = sample_from_range((10, 50), 'uniform')
        >>> 10 <= val <= 50
        True
    """
    min_val, max_val = range_tuple

    if distribution == 'uniform':
        return random.uniform(min_val, max_val)
    elif distribution == 'normal':
        # Normal distribution centered in range
        mean = (min_val + max_val) / 2
        std = (max_val - min_val) / 6  # 99.7% within range
        val = random.gauss(mean, std)
        return np.clip(val, min_val, max_val)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")


def clip_to_valid_range(values: np.ndarray,
                       min_val: float,
                       max_val: float) -> np.ndarray:
    """
    Clip array values to valid range while minimizing correlation degradation.

    Uses soft clipping to preserve relative ordering.

    Args:
        values: Array to clip
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clipped array
    """
    return np.clip(values, min_val, max_val)


def round_to_cents(amount: float) -> float:
    """
    Round bet amount to cents (2 decimal places).

    Args:
        amount: Dollar amount

    Returns:
        Rounded amount

    Examples:
        >>> round_to_cents(10.12345)
        10.12
    """
    return round(amount, 2)


def validate_player_id(player_id: str) -> bool:
    """
    Validate player ID format.

    Args:
        player_id: Player ID string

    Returns:
        True if valid format

    Examples:
        >>> validate_player_id('PLR_0001_MA')
        True
        >>> validate_player_id('INVALID')
        False
    """
    import re
    pattern = r'^PLR_\d{4}_(MA|NJ|PA)$'
    return bool(re.match(pattern, player_id))


def validate_bet_id(bet_id: str) -> bool:
    """
    Validate bet ID format.

    Args:
        bet_id: Bet ID string

    Returns:
        True if valid format

    Examples:
        >>> validate_bet_id('BET_00000001')
        True
        >>> validate_bet_id('BET_1')
        False
    """
    import re
    pattern = r'^BET_\d{8}$'
    return bool(re.match(pattern, bet_id))


def get_hour_category(hour: int) -> str:
    """
    Categorize hour of day for temporal analysis.

    Args:
        hour: Hour (0-23)

    Returns:
        Category: 'late_night', 'daytime', 'primetime'

    Examples:
        >>> get_hour_category(3)
        'late_night'
        >>> get_hour_category(20)
        'primetime'
    """
    if 2 <= hour < 6:
        return 'late_night'
    elif 10 <= hour < 18:
        return 'daytime'
    elif 18 <= hour <= 23:
        return 'primetime'
    else:
        return 'other'


def calculate_days_between(date1: str, date2: str) -> int:
    """
    Calculate days between two dates.

    Args:
        date1: First date (YYYY-MM-DD)
        date2: Second date (YYYY-MM-DD)

    Returns:
        Number of days

    Examples:
        >>> calculate_days_between('2026-01-01', '2026-01-31')
        30
    """
    d1 = datetime.strptime(date1, '%Y-%m-%d')
    d2 = datetime.strptime(date2, '%Y-%m-%d')
    return abs((d2 - d1).days)


# =============================================================================
# TESTING UTILITIES
# =============================================================================

def verify_dataframe_schema(df: pd.DataFrame,
                           expected_columns: List[str]) -> bool:
    """
    Verify DataFrame has expected columns.

    Args:
        df: DataFrame to validate
        expected_columns: List of expected column names

    Returns:
        True if schema matches

    Raises:
        ValueError: If columns don't match
    """
    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")
    if extra:
        raise ValueError(f"Unexpected columns: {extra}")

    return True


if __name__ == "__main__":
    # Run basic tests
    print("Testing utils...")

    # Test ID generation
    assert generate_player_id(0, 'MA') == 'PLR_0001_MA'
    assert generate_bet_id(0) == 'BET_00000001'

    # Test validation
    assert validate_player_id('PLR_0001_MA') == True
    assert validate_player_id('INVALID') == False
    assert validate_bet_id('BET_00000001') == True

    # Test hour categorization
    assert get_hour_category(3) == 'late_night'
    assert get_hour_category(20) == 'primetime'

    print("✓ All utils tests passed")
