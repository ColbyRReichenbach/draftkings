"""
DK Sentinel Synthetic Data Generation Package

Generates 10,000 players with 500,000 bets exhibiting research-backed
responsible gambling patterns for portfolio demonstration.

Key features:
- Cholesky decomposition for multivariate correlations
- State machine for loss-chasing behavior
- 10 edge cases for pipeline robustness testing
- Statistical validation (chi-square, K-S tests, correlation validation)

Usage:
    python -m data_generation --output-dir data/ --validate

For more information, see data_generation/DATA.md
"""

__version__ = "1.0.0"
__author__ = "DK Sentinel Team"

# Package metadata
PACKAGE_NAME = "dk_sentinel_data_generation"
