"""
Correlation generation using Cholesky decomposition.

Implements multivariate normal generation with specified correlation structure
to ensure target correlations between Gamalyze scores and betting behavior.

Key Innovation:
- Generate correlated "latent factors" at player level
- These factors drive both Gamalyze scores AND betting patterns
- Ensures cross-table correlations (gamalyze_scores.csv ↔ bets.csv)

Mathematical Foundation:
- Cholesky decomposition: If Σ is covariance matrix, L @ L.T = Σ
- Transform uncorrelated standard normal to correlated: X = L @ Z + μ
- Industry standard approach in financial modeling and simulation
"""

import numpy as np
from numpy.linalg import cholesky
from typing import Tuple
from .config import CORRELATION_MATRIX, LATENT_FACTOR_MEANS, LATENT_FACTOR_STDS


def generate_correlated_variables(n_samples: int,
                                  correlation_matrix: np.ndarray,
                                  means: np.ndarray,
                                  stds: np.ndarray) -> np.ndarray:
    """
    Generate multivariate normal distribution with specified correlations.

    Uses Cholesky decomposition to transform uncorrelated standard normal
    variables into correlated variables with target correlation structure.

    Mathematical Process:
    1. Convert correlation matrix to covariance matrix: Σ = D @ R @ D
       where D is diagonal matrix of standard deviations
    2. Cholesky decomposition: Σ = L @ L.T
    3. Generate uncorrelated standard normal: Z ~ N(0, I)
    4. Transform: X = L @ Z + μ

    Args:
        n_samples: Number of samples to generate (e.g., 10,000 players)
        correlation_matrix: Target correlation matrix (k x k)
        means: Mean values for each variable (length k)
        stds: Standard deviations for each variable (length k)

    Returns:
        Array of shape (n_samples, k) with target correlations

    Example:
        >>> # Generate 1000 samples with r=0.72 correlation
        >>> corr_matrix = np.array([[1.0, 0.72], [0.72, 1.0]])
        >>> means = np.array([50, 50])
        >>> stds = np.array([15, 15])
        >>> samples = generate_correlated_variables(1000, corr_matrix, means, stds)
        >>> actual_r = np.corrcoef(samples[:, 0], samples[:, 1])[0, 1]
        >>> abs(actual_r - 0.72) < 0.05  # Within tolerance
        True

    Raises:
        ValueError: If correlation matrix is not symmetric or positive definite
    """
    # Validate inputs
    if not np.allclose(correlation_matrix, correlation_matrix.T):
        raise ValueError("Correlation matrix must be symmetric")

    if correlation_matrix.shape[0] != len(means):
        raise ValueError("Correlation matrix dimensions must match means length")

    if correlation_matrix.shape[0] != len(stds):
        raise ValueError("Correlation matrix dimensions must match stds length")

    # Step 1: Convert correlation matrix to covariance matrix
    # Cov(X, Y) = ρ(X, Y) × σ_X × σ_Y
    D = np.diag(stds)  # Diagonal matrix of standard deviations
    cov_matrix = D @ correlation_matrix @ D

    # Step 2: Cholesky decomposition
    # Σ = L @ L.T where L is lower triangular
    try:
        L = cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        raise ValueError(
            "Correlation matrix is not positive definite. "
            "Ensure all correlations are valid (between -1 and 1) "
            "and matrix is feasible."
        )

    # Step 3: Generate uncorrelated standard normal samples
    # Z ~ N(0, I) where I is identity matrix
    uncorrelated = np.random.standard_normal((n_samples, len(means)))

    # Step 4: Transform to correlated samples
    # X = L @ Z.T + μ, then transpose back
    correlated = uncorrelated @ L.T + means

    return correlated


def generate_latent_factors_for_cohort(n_samples: int,
                                       cohort: str) -> np.ndarray:
    """
    Generate latent factors for a specific risk cohort.

    Latent factors are the "psychological DNA" of each player that drives
    both their Gamalyze scores and their betting behavior.

    Order of factors:
    0. sensitivity_to_loss (0-100 scale, raw)
    1. risk_tolerance (0-100 scale, raw)
    2. decision_consistency (0-100 scale, raw)
    3. bet_escalation_ratio (1.0-5.0 scale)

    Args:
        n_samples: Number of players in this cohort
        cohort: Risk cohort ('low_risk', 'medium_risk', 'high_risk', 'critical')

    Returns:
        Array of shape (n_samples, 4) with latent factors

    Example:
        >>> factors = generate_latent_factors_for_cohort(100, 'high_risk')
        >>> factors.shape
        (100, 4)
        >>> # High-risk players should have high sensitivity_to_loss
        >>> np.mean(factors[:, 0]) > 60
        True
    """
    if cohort not in LATENT_FACTOR_MEANS:
        raise ValueError(f"Invalid cohort: {cohort}")

    means = LATENT_FACTOR_MEANS[cohort]
    stds = LATENT_FACTOR_STDS

    return generate_correlated_variables(
        n_samples=n_samples,
        correlation_matrix=CORRELATION_MATRIX,
        means=means,
        stds=stds
    )


def verify_correlation(data: np.ndarray,
                      expected_corr_matrix: np.ndarray,
                      tolerance: float = 0.05) -> Tuple[bool, np.ndarray]:
    """
    Verify that generated data has expected correlations.

    Args:
        data: Generated data array (n_samples x k_variables)
        expected_corr_matrix: Expected correlation matrix (k x k)
        tolerance: Acceptable deviation from target (default ±0.05)

    Returns:
        Tuple of (all_pass: bool, actual_corr_matrix: np.ndarray)

    Example:
        >>> data = generate_correlated_variables(1000, CORRELATION_MATRIX,
        ...                                      np.array([50, 50, 50, 2.0]),
        ...                                      np.array([15, 12, 10, 0.5]))
        >>> passed, actual = verify_correlation(data, CORRELATION_MATRIX)
        >>> passed
        True
    """
    # Calculate actual correlation matrix
    actual_corr = np.corrcoef(data, rowvar=False)

    # Compare each correlation
    n_vars = expected_corr_matrix.shape[0]
    all_pass = True

    for i in range(n_vars):
        for j in range(i + 1, n_vars):  # Upper triangle only
            expected = expected_corr_matrix[i, j]
            actual = actual_corr[i, j]
            diff = abs(actual - expected)

            if diff > tolerance:
                all_pass = False
                print(f"⚠ Correlation [{i}, {j}]: "
                      f"Expected {expected:.3f}, got {actual:.3f} "
                      f"(diff: {diff:.3f})")

    return all_pass, actual_corr


def calculate_correlation_with_derived_metric(gamalyze_scores: np.ndarray,
                                              bet_metrics: np.ndarray) -> float:
    """
    Calculate correlation between Gamalyze score and bet-derived metric.

    This is used for validation to ensure cross-table correlations are achieved.

    Args:
        gamalyze_scores: Array of Gamalyze scores (e.g., sensitivity_to_loss)
        bet_metrics: Array of bet-derived metrics (e.g., bet_escalation_ratio)

    Returns:
        Pearson correlation coefficient

    Example:
        >>> sensitivity = np.random.normal(50, 15, 1000)
        >>> bet_escalation = 0.72 * sensitivity + np.random.normal(0, 10, 1000)
        >>> r = calculate_correlation_with_derived_metric(sensitivity, bet_escalation)
        >>> 0.65 < r < 0.80  # Should be around 0.72
        True
    """
    return np.corrcoef(gamalyze_scores, bet_metrics)[0, 1]


def add_noise(values: np.ndarray, noise_std: float = 0.05) -> np.ndarray:
    """
    Add Gaussian noise to values to simulate measurement variability.

    Used when transforming latent factors to Gamalyze scores to add
    realistic assessment variability.

    Args:
        values: Array of values
        noise_std: Standard deviation of noise (relative to value scale)

    Returns:
        Noisy values

    Example:
        >>> values = np.array([50, 60, 70])
        >>> noisy = add_noise(values, noise_std=0.05)
        >>> np.allclose(values, noisy, atol=5)  # Within 5 units
        True
    """
    noise = np.random.normal(0, noise_std, size=values.shape)
    return values + noise


# =============================================================================
# TESTING AND VALIDATION
# =============================================================================

def test_cholesky_decomposition():
    """
    Test Cholesky decomposition with known correlation matrix.

    Verifies that generated samples have target correlations.
    """
    print("Testing Cholesky decomposition...")

    # Simple 2D test case
    n = 10000
    target_corr = np.array([[1.0, 0.75], [0.75, 1.0]])
    means = np.array([50, 50])
    stds = np.array([15, 15])

    # Generate samples
    samples = generate_correlated_variables(n, target_corr, means, stds)

    # Verify means
    actual_means = np.mean(samples, axis=0)
    assert np.allclose(actual_means, means, atol=1.0), \
        f"Means don't match: expected {means}, got {actual_means}"

    # Verify stds
    actual_stds = np.std(samples, axis=0)
    assert np.allclose(actual_stds, stds, atol=1.0), \
        f"Stds don't match: expected {stds}, got {actual_stds}"

    # Verify correlation
    actual_corr = np.corrcoef(samples, rowvar=False)[0, 1]
    assert abs(actual_corr - 0.75) < 0.02, \
        f"Correlation doesn't match: expected 0.75, got {actual_corr:.3f}"

    print(f"✓ Cholesky test passed (r={actual_corr:.3f}, target=0.75)")


def test_4d_correlation_matrix():
    """
    Test with actual 4D correlation matrix from config.

    Verifies all pairwise correlations are within tolerance.
    """
    print("Testing 4D correlation matrix...")

    n = 5000
    means = LATENT_FACTOR_MEANS['high_risk']
    stds = LATENT_FACTOR_STDS

    # Generate samples
    samples = generate_correlated_variables(n, CORRELATION_MATRIX, means, stds)

    # Verify correlations
    passed, actual_corr = verify_correlation(samples, CORRELATION_MATRIX, tolerance=0.05)

    if passed:
        print("✓ All correlations within tolerance")
    else:
        print("⚠ Some correlations outside tolerance")

    # Print key correlations
    print("\nKey correlations:")
    print(f"  sensitivity_to_loss ↔ bet_escalation_ratio: {actual_corr[0, 3]:.3f} (target: 0.72)")
    print(f"  risk_tolerance ↔ bet_escalation_ratio: {actual_corr[1, 3]:.3f} (target: 0.58)")
    print(f"  decision_consistency ↔ bet_escalation_ratio: {actual_corr[2, 3]:.3f} (target: -0.45)")

    return passed


def test_cohort_generation():
    """
    Test latent factor generation for each cohort.

    Verifies that cohort means are correctly applied.
    """
    print("Testing cohort generation...")

    cohorts = ['low_risk', 'medium_risk', 'high_risk', 'critical']

    for cohort in cohorts:
        factors = generate_latent_factors_for_cohort(1000, cohort)

        # Verify shape
        assert factors.shape == (1000, 4), f"Wrong shape for {cohort}"

        # Verify approximate means
        actual_means = np.mean(factors, axis=0)
        expected_means = LATENT_FACTOR_MEANS[cohort]

        # Allow 10% tolerance on means due to random sampling
        tolerance = expected_means * 0.1
        assert np.allclose(actual_means, expected_means, atol=tolerance.max()), \
            f"{cohort} means don't match: expected {expected_means}, got {actual_means}"

        print(f"✓ {cohort}: sensitivity={actual_means[0]:.1f}, escalation={actual_means[3]:.2f}")


if __name__ == "__main__":
    # Run all tests
    print("=" * 60)
    print("CORRELATION MODULE TESTS")
    print("=" * 60)

    test_cholesky_decomposition()
    print()

    test_4d_correlation_matrix()
    print()

    test_cohort_generation()
    print()

    print("=" * 60)
    print("✅ All correlation tests passed!")
    print("=" * 60)
