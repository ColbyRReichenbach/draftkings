# DK Sentinel: Weekly Progress Tracker

## Week 1: Data Foundation ✓ COMPLETE

**Goals**:
- [x] Generate synthetic data (10K players, ~500K bets)
- [x] Create dbt project structure (medallion: staging → intermediate → marts)
- [x] Load data to DuckDB (dev target; Snowflake profile stubbed for Week 5 migration)
- [x] Validate staging layer (51/51 dbt tests passing)

**Delivered**:
- 3 staging views: `stg_bet_logs`, `stg_player_profiles`, `stg_gamalyze_scores`
- Full data contract enforcement via `schema.yml` (unique, not_null, accepted_values, relationships, accepted_range)
- Data generation pipeline: `python -m data_generation` → `python scripts/load_to_duckdb.py`
- SQL compatibility score 100/100 — staging layer is Snowflake-portable as-is
- Pipeline executes in <4s on DuckDB (models 0.7s + tests 2.9s)

**Bug fixed**: `schema.yml` `accepted_values` for `risk_cohort` had `CRITICAL_RISK`; generator emits `critical` → `UPPER()` → `CRITICAL`. Corrected to match.

**Known issues (not blocking)**:
- Bet count was ~216K (below target). **Resolved** by extending the generation window to 90 days; current output ~500K bets.
- Generator validation Tier 3 (distributions) and Tier 4 (correlations) fail. Two of three target correlations are attenuated by the state machine in `bet_generator.py`. Documented in `DATA_GENERATION_METHODOLOGY.md`.
- Edge case injection is stubbed — 10 edge cases defined in `edge_cases.py` but not yet applied to output.

**Next Week Preview**: Intermediate models (loss-chasing indicators, market drift features)

---

## Week 2: Intermediate Models ✓ COMPLETE

**Goals**:
- [x] Build loss-chasing indicators (bet-after-loss + escalation)
- [x] Build market drift indicators (horizontal/vertical/temporal)
- [x] Build Gamalyze composite score (latest 90-day assessment)
- [x] Enforce tests + schema documentation for new models
- [x] Run full dbt test suite

**Delivered**:
- Intermediate models:
  - `int_loss_chasing_indicators`
  - `int_market_drift_indicators`
  - `int_gamalyze_composite`
- Added local `accepted_range` test macro (offline-safe; no dbt_utils dependency)
- Singular tests:
  - `assert_loss_chasing_min_bets`
  - `assert_loss_chasing_ratios_valid`
  - `assert_market_drift_ratios_valid`
  - `assert_gamalyze_score_bounds`
- Validation: `dbt test` 101/101 passing

**Notes**:
- Removed external dbt package dependency to keep offline dev environment stable.

**Next Week Preview**: Marts layer (composite risk scores + categories)

---

## Week 3: Marts Layer ✓ COMPLETE

**Goals**:
- [x] Build composite risk score mart (`rg_risk_scores`)
- [x] Add marts schema tests + singular validations
- [x] Validate full dbt test suite

**Delivered**:
- `rg_risk_scores` marts model with normalization + weight application
- Tests:
  - `assert_component_scores_in_range`
  - `assert_risk_weights_sum_to_one`
  - `assert_risk_category_thresholds`
- Validation: `dbt test` 121/121 passing

**Next Week Preview**: Compliance review + analyst workflow integration

---

## Week 4: [TBD]
**In Progress**:
- [x] Compliance foundation: `rg_audit_trail`
- [x] Analyst queue: `rg_intervention_queue`
- [x] Full dbt validation (152/152 tests)
 - [x] Data generator tuning to better surface HIGH/CRITICAL risk categories (documented rationale)

---

[Continue through Week 8]
