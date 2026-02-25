# DK Sentinel Data Generation

Synthetic data generator for responsible gambling analytics portfolio project.

## Overview

Generates 10,000 players with approximately 500,000 bets and synthetic behavioral patterns including:
- Statistical correlations (Cholesky decomposition)
- Loss-chasing behavior (finite state machine)
- Market drift patterns (NFL → Table Tennis for high-risk players)
- Temporal patterns (late-night betting escalation)
- 10 edge cases for pipeline robustness testing

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate full dataset (10K players, ~500K bets)
python -m data_generation

# Generate to specific directory
python -m data_generation --output-dir data/

# Generate smaller test dataset
python -m data_generation --n-players 100 --output-dir data/test

# Skip validation (faster)
python -m data_generation --no-validate
```

## Output Files

Generates three CSV files in `data/` directory:

### 1. `players.csv` (10,000 rows, ~0.6 MB)
```csv
player_id,first_name,last_name,email,age,state,risk_cohort
PLR_0001_MA,John,Doe,john.doe@example.com,35,MA,low_risk
```

**Columns**:
- `player_id`: Unique ID (format: PLR_####_{STATE})
- `first_name`, `last_name`, `email`: Realistic demographics (Faker)
- `age`: 21-75 (legal betting age)
- `state`: MA, NJ, or PA (regulatory focus states)
- `risk_cohort`: low_risk (90%), medium_risk (8%), high_risk (1.5%), critical (0.5%)

### 2. `bets.csv` (~500,000 rows)
```csv
bet_id,player_id,bet_timestamp,sport_category,market_type,bet_amount,odds_american,outcome
BET_00000001,PLR_0001_MA,2026-01-02T20:15:33,NFL,moneyline,45.50,-110,win
```

**Columns**:
- `bet_id`: Unique ID (format: BET_########)
- `player_id`: Foreign key to players
- `bet_timestamp`: ISO 8601 timestamp
- `sport_category`: NFL, NBA, MLB, NHL, SOCCER, MMA, TENNIS, TABLE_TENNIS
- `market_type`: moneyline (simplified)
- `bet_amount`: Dollars (minimum $0.01)
- `odds_american`: American odds format (e.g., -110, +150)
- `outcome`: win or loss

### 3. `gamalyze_scores.csv` (10,000 rows, ~0.7 MB)
```csv
assessment_id,player_id,assessment_date,sensitivity_to_loss,sensitivity_to_reward,risk_tolerance,decision_consistency,gamalyze_version
ASSESS_PLR_0001_MA,PLR_0001_MA,2025-12-15,32.45,41.22,28.76,72.15,v3.2.1
```

**Columns**:
- `assessment_id`: Unique ID per assessment
- `player_id`: Foreign key to players
- `assessment_date`: Date of assessment (random past 90 days)
- `sensitivity_to_loss`: 0-100 scale (neuro-marker)
- `sensitivity_to_reward`: 0-100 scale
- `risk_tolerance`: 0-100 scale
- `decision_consistency`: 0-100 scale
- `gamalyze_version`: v3.2.1

**Note**: PLR_0333_NJ is defined as an edge case for missing data handling but edge case injection is not yet fully implemented — all 10,000 scores are currently generated.

## Key Features

### 1. Pattern Design Inputs

- **Prevalence mix**: portfolio-oriented cohort mix tuned for sufficient review cases
- **Sport distribution targets**: weighted toward major US markets with niche tails
- **Temporal patterns**: elevated late-night behavior in higher-risk cohorts
- **Neuro-marker component**: synthetic Gamalyze-style score generation

### 2. Statistical Correlations (Current State)

Target correlations are seeded via Cholesky decomposition, then attenuated by downstream state-machine behavior:

| Variables | Target r | Achieved r | Status |
|-----------|----------|------------|--------|
| sensitivity_to_loss ↔ bet_escalation_ratio | 0.72 | 0.374 | needs tuning |
| risk_tolerance ↔ market_tier_drift | 0.58 | -0.214 | needs tuning |
| decision_consistency ↔ temporal_risk | -0.45 | -0.467 | ✓ |

### 3. Loss-Chasing State Machine

```
NORMAL --[loss + probability]--> CHASING --[loss]--> ESCALATING
       <--[win]--                        <--[win]--
```

- NORMAL: Base bet amount ± 20% variance
- CHASING: Base × target_escalation_ratio (e.g., 2.5x)
- ESCALATING: Base × ratio^consecutive_losses (capped at 5x)

### 4. Market Drift

High-risk players progressively shift from major sports to niche markets:

- t=0.0 (start): NFL 40%, TABLE_TENNIS 1%
- t=0.5 (mid): NFL 35%, TABLE_TENNIS 5%
- t=1.0 (end): NFL 27%, TABLE_TENNIS 16%

### 5. Temporal Patterns

- Normal players: Peak at 8 PM (primetime)
- Chasing players: Bimodal distribution
  - 60% primetime
  - 40% late-night (2-6 AM) during severe chasing

### 5b. Outcome Probabilities (By Cohort)

To align loss-chasing ratios with business logic thresholds, win rates vary by cohort:
- low_risk: 0.47
- medium_risk: 0.45
- high_risk: 0.35
- critical: 0.30

Rationale: Higher-risk cohorts are modeled as selecting longer-odds markets, which lowers win rates
and increases bet-after-loss ratios without changing scoring thresholds.

Additional tuning:
- `target_bet_escalation` is clamped to cohort ranges for consistent escalation behavior
- Market drift accelerates late in the window to better surface vertical/horizontal drift
- Bet timestamps are enforced to be non-decreasing to preserve loss-chasing sequence order
- Bet generation stops at the end of the window to avoid timestamp clustering

### 6. Edge Cases

10 special test cases for pipeline robustness (see `edge_cases.py`):

1. PLR_0001_MA: 100% win rate
2. PLR_0002_NJ: 100% loss rate
3. PLR_0003_PA: Single bet only
4. PLR_0042_MA: Table Tennis only
5. PLR_0099_NJ: 3 AM betting only
6. PLR_0156_MA: $0.01 bets (penny bettor)
7. PLR_0203_PA: $10,000 bets (whale)
8. PLR_0333_NJ: Missing Gamalyze score
9. PLR_0405_MA: NULL sport in some bets
10. PLR_0500_PA: Self-exclusion reversal

## Module Architecture

```
data_generation/
├── __init__.py            # Package metadata
├── __main__.py            # CLI entry point (orchestration)
├── config.py              # Central configuration (constants, distributions)
├── utils.py               # Helper functions (ID generation, date utils)
├── correlations.py        # Cholesky decomposition engine
├── player_generator.py    # Player cohorts + latent factors
├── gamalyze_generator.py  # Neuro-marker score transformation
├── bet_generator.py       # State machine for betting sequences
├── edge_cases.py          # 10 special test cases
└── validation.py          # Statistical validation suite
```

## Validation

The generator includes a validation suite:

**Tier 1: Count Validations**
- Players: Exactly 10,000
- Bets: ~500,000 (driven by per-cohort `bets_per_week` over a 90-day window; `TARGET_TOTAL_BETS` is not enforced)
- Gamalyze: 10,000 (edge case removal not yet implemented)

**Tier 2: Data Quality**
- No NULL player IDs
- All states in {MA, NJ, PA}
- All bet amounts > $0

**Tier 3: Distributions**
- Distribution checks are advisory in this portfolio project and can fail depending on sample dynamics and tuning.

**Tier 4: Correlations**
- Correlation checks are advisory; not all targets currently converge within ±0.05.

Run validation:
```bash
python -m data_generation --validate  # Default: enabled
python -m data_generation --no-validate  # Skip for speed
```

## Performance

Benchmarks on MacBook Pro M1 (90-day window; approximate, non-SLA):

| Players | Bets | Time |
|---------|------|------|
| 100 | ~2K | ~1s |
| 1,000 | ~20K | ~2s |
| 10,000 | ~500K | ~30s |

**Bottleneck**: Bet generation (state machine requires sequential processing)

## Reproducibility

Fixed random seed (42) ensures reproducible generation:

```bash
python -m data_generation --seed 42  # Same data every time
python -m data_generation --seed 123  # Different data, same statistics
```

## Integration with Local Pipeline

After generation, load into the local DuckDB pipeline:

```sql
python scripts/load_to_duckdb.py
```

Then run dbt transforms:

```bash
dbt run
dbt test
```

## Troubleshooting

**ImportError: No module named 'faker'**
```bash
pip install -r requirements.txt
```

**Validation tests failing**
- For small samples (<1000 players), checks may fail due to sampling variance.
- Tier 3/4 checks are advisory and may fail at 10K depending on tuning.
- See `docs/DATA_GENERATION_METHODOLOGY.md` for current limitations.

**Slow generation**
- Use `--n-players 100` for faster testing
- Use `--no-validate` to skip validation
- Bet generation scales linearly with player count

## Testing Individual Modules

Each module can be tested independently:

```bash
# Test correlations (Cholesky decomposition)
python -m data_generation.correlations

# Test player generation
python -m data_generation.player_generator

# Test Gamalyze scores
python -m data_generation.gamalyze_generator

# Test bet generation (state machine)
python -m data_generation.bet_generator

# View edge case definitions
python -m data_generation.edge_cases
```

## License

Internal portfolio project - not for production use.

## Contact

For questions about data generation methodology, see `docs/DATA_GENERATION_METHODOLOGY.md`.

---

**Last Updated**: February 2026
**Version**: 1.0.0
