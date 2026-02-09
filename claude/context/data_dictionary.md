# Data Dictionary

**Purpose**: Complete reference for all tables, columns, and data types in DK Sentinel

**Last Updated**: 2026-02-01

---

## Database Hierarchy
````
RG_ANALYTICS (Database)
├── STAGING (Schema) - Raw data with light transformations
├── PROD (Schema) - Production models
└── ANALYTICS (Schema) - Reporting views and aggregations
````

---

## DuckDB Dev Snapshot (Authoritative for This Repo)
**Generated**: 2026-02-04  
**Note**: The live DuckDB schema is the source of truth for app/LLM queries.  
If a column is not listed here, it is **not available** in the dev environment.

### STAGING.STG_BET_LOGS (physical: `staging_staging.stg_bet_logs`)
`bet_id`, `player_id`, `bet_timestamp`, `sport_category`, `market_type`, `bet_amount`, `odds_american`, `outcome`

### STAGING.STG_PLAYER_PROFILES (physical: `staging_staging.stg_player_profiles`)
`player_id`, `first_name`, `last_name`, `email`, `age`, `state_jurisdiction`, `risk_cohort`

### STAGING.STG_GAMALYZE_SCORES (physical: `staging_staging.stg_gamalyze_scores`)
`assessment_id`, `player_id`, `assessment_date`, `sensitivity_to_reward`, `sensitivity_to_loss`,
`risk_tolerance`, `decision_consistency`, `overall_risk_rating`, `loaded_at`, `gamalyze_version`

### PROD.RG_RISK_SCORES (physical: `staging_prod.rg_risk_scores`)
`player_id`, `loss_chase_score`, `bet_escalation_score`, `market_drift_score`, `temporal_risk_score`,
`gamalyze_risk_score`, `composite_risk_score`, `risk_category`, `calculated_at`

### PROD.RG_INTERVENTION_QUEUE (physical: `staging_prod.rg_intervention_queue`)
`player_id`, `composite_risk_score`, `risk_category`, `primary_driver`, `loss_chase_score`, `bet_escalation_score`,
`market_drift_score`, `temporal_risk_score`, `gamalyze_risk_score`, `calculated_at`

---

## STAGING Layer

### STG_BET_LOGS

**Purpose**: Cleaned and standardized bet transaction logs

**Grain**: One row per bet

**Materialization**: View (refreshes from raw data)

**Source**: `RAW.BET_TRANSACTIONS` (upstream system)

| Column | Data Type | Description | Constraints | Example |
|--------|-----------|-------------|-------------|---------|
| `bet_id` | VARCHAR(50) | Unique bet identifier | PK, NOT NULL | "BET_2026_001234" |
| `player_id` | VARCHAR(50) | Unique player identifier | FK → STG_PLAYER_PROFILES, NOT NULL | "PLR_1234_MA" |
| `bet_timestamp` | TIMESTAMP_NTZ | When bet was placed (ET timezone) | NOT NULL | "2026-01-15 19:30:45" |
| `bet_amount` | DECIMAL(10,2) | Wager amount in USD | NOT NULL, >0 | 50.00 |
| `sport_category` | VARCHAR(50) | Sport type (standardized uppercase) | NOT NULL | "NFL", "NBA", "TABLE_TENNIS" |
| `market_type` | VARCHAR(100) | Specific bet market | NOT NULL | "Moneyline", "Point Spread", "Parlay" |
| `outcome` | VARCHAR(20) | Bet result | NOT NULL, IN ('win', 'loss', 'push', 'pending') | "loss" |
| `payout_amount` | DECIMAL(10,2) | Winnings amount (0 for losses) | NOT NULL, >=0 | 0.00 |
| `market_tier` | DECIMAL(3,1) | Market quality tier (see business_logic.md) | NOT NULL, IN (1.0, 0.7, 0.5, 0.2) | 1.0 |
| `state_jurisdiction` | CHAR(2) | State where bet was placed | NOT NULL, IN ('MA', 'NJ', 'PA') | "MA" |
| `bet_sequence_num` | INT | Player's sequential bet number | NOT NULL | 47 |
| `loaded_at` | TIMESTAMP_NTZ | When row was loaded to staging | NOT NULL | "2026-01-15 20:00:00" |

**Data Quality Rules**:
- `bet_amount` must be positive
- `bet_timestamp` must be within last 90 days (older bets archived)
- `outcome` = 'pending' excluded from behavioral analytics
- `sport_category` standardized via `UPPER(TRIM())` transformation

**Row Count**: ~500K active bets (90-day rolling window)

---

### STG_PLAYER_PROFILES

**Purpose**: Player demographic and account information

**Grain**: One row per player

**Materialization**: View

**Source**: `RAW.PLAYER_ACCOUNTS`

| Column | Data Type | Description | Constraints | Example |
|--------|-----------|-------------|-------------|---------|
| `player_id` | VARCHAR(50) | Unique player identifier | PK, NOT NULL | "PLR_1234_MA" |
| `account_created_date` | DATE | When account was created | NOT NULL | "2024-06-15" |
| `state_jurisdiction` | CHAR(2) | Player's home state | NOT NULL | "MA" |
| `age` | INT | Player age in years | NOT NULL, >=21 | 34 |
| `self_excluded` | BOOLEAN | Currently self-excluded flag | NOT NULL | FALSE |
| `self_exclusion_history` | ARRAY | List of exclusion periods | NULLABLE | [{"start": "2025-03-01", "end": "2025-06-01"}] |
| `account_status` | VARCHAR(20) | Account state | NOT NULL, IN ('active', 'suspended', 'closed') | "active" |
| `updated_at` | TIMESTAMP_NTZ | Last profile update | NOT NULL | "2026-01-15 18:00:00" |

**Row Count**: ~10K active players

---

### STG_GAMALYZE_SCORES

**Purpose**: Mindway AI neuro-marker assessments

**Grain**: One row per player per assessment

**Materialization**: View

**Source**: `RAW.GAMALYZE_ASSESSMENTS` (via API integration)

| Column | Data Type | Description | Constraints | Example |
|--------|-----------|-------------|-------------|---------|
| `assessment_id` | VARCHAR(50) | Unique assessment identifier | PK, NOT NULL | "GMLY_2026_001234" |
| `player_id` | VARCHAR(50) | Player assessed | FK → STG_PLAYER_PROFILES, NOT NULL | "PLR_1234_MA" |
| `assessment_date` | DATE | Date of assessment | NOT NULL | "2026-01-15" |
| `sensitivity_to_reward` | INT | Neuro-marker score (0-100) | NOT NULL, 0-100 | 68 |
| `sensitivity_to_loss` | INT | Neuro-marker score (0-100) | NOT NULL, 0-100 | 82 |
| `risk_tolerance` | INT | Neuro-marker score (0-100) | NOT NULL, 0-100 | 75 |
| `decision_consistency` | INT | Neuro-marker score (0-100, higher=better) | NOT NULL, 0-100 | 42 |
| `gamalyze_version` | VARCHAR(20) | Gamalyze model version | NOT NULL | "v3.2.1" |
| `overall_risk_rating` | VARCHAR(20) | Gamalyze's overall assessment | NOT NULL | "HIGH_RISK" |
| `loaded_at` | TIMESTAMP_NTZ | When loaded to staging | NOT NULL | "2026-01-15 20:30:00" |

**Data Quality Rules**:
- All scores must be 0-100 (enforced by source API)
- One assessment per player per day (deduped by most recent)
- Players without assessment: use population median (50) as default

**Row Count**: ~10K (one per active player, updated monthly)

---

## PROD Layer (Intermediate)

### INT_LOSS_CHASING_INDICATORS

**Purpose**: Behavioral metrics for loss-chasing detection

**Grain**: One row per player

**Materialization**: Incremental (on `bet_timestamp`)

**Source**: `STG_BET_LOGS`

| Column | Data Type | Description | Formula | Example |
|--------|-----------|-------------|---------|---------|
| `player_id` | VARCHAR(50) | Unique player identifier | PK | "PLR_1234_MA" |
| `total_bets` | INT | Total bets in 7-day window | COUNT(*) | 45 |
| `bets_after_loss` | INT | Bets placed after losses | COUNT(*) FILTER (prev_outcome='loss') | 34 |
| `bets_after_win` | INT | Bets placed after wins | COUNT(*) FILTER (prev_outcome='win') | 11 |
| `bet_after_loss_ratio` | DECIMAL(5,4) | Proportion of bets after losses | bets_after_loss / total_bets | 0.7556 |
| `avg_bet_after_loss` | DECIMAL(10,2) | Average bet size after losses | AVG(bet_amount) FILTER (prev_outcome='loss') | 127.50 |
| `avg_bet_after_win` | DECIMAL(10,2) | Average bet size after wins | AVG(bet_amount) FILTER (prev_outcome='win') | 62.30 |
| `bet_escalation_ratio` | DECIMAL(5,2) | Bet size increase after losses | avg_bet_after_loss / avg_bet_after_win | 2.05 |
| `last_bet_timestamp` | TIMESTAMP_NTZ | Most recent bet timestamp (for incremental) | MAX(bet_timestamp) | "2026-01-15 22:15:00" |
| `calculated_at` | TIMESTAMP_NTZ | When this row was calculated | CURRENT_TIMESTAMP() | "2026-01-15 23:00:00" |

**Incremental Logic**:
````sql
{% if is_incremental() %}
WHERE bet_timestamp > (SELECT MAX(last_bet_timestamp) FROM {{ this }})
{% endif %}
````

**Data Quality**:
- Excludes players with <2 bets (insufficient data for ratios)
- `bet_escalation_ratio` capped at 10.0 (prevents division issues)

**Row Count**: ~10K active players

---

### INT_MARKET_DRIFT_DETECTION

**Purpose**: Sport diversity, market tier, and time-of-day drift metrics

**Grain**: One row per player

**Materialization**: Incremental

| Column | Data Type | Description | Formula | Example |
|--------|-----------|-------------|---------|---------|
| `player_id` | VARCHAR(50) | Unique player identifier | PK | "PLR_1234_MA" |
| `unique_sports_7d` | INT | Distinct sports bet on (7 days) | COUNT(DISTINCT sport_category) | 6 |
| `baseline_sports_90d` | DECIMAL(5,2) | Rolling 90-day average sport count | AVG(unique_sports) OVER (90 days) | 2.0 |
| `sport_diversity_ratio` | DECIMAL(5,2) | Horizontal drift metric | unique_sports_7d / baseline_sports_90d | 3.0 |
| `avg_market_tier_7d` | DECIMAL(3,2) | Current week market tier | AVG(market_tier) | 0.35 |
| `baseline_market_tier_90d` | DECIMAL(3,2) | Baseline market tier | AVG(market_tier) OVER (90 days) | 0.95 |
| `market_tier_drop_pct` | DECIMAL(5,4) | Vertical drift metric | (baseline - current) / baseline | 0.6316 |
| `bets_2am_to_6am` | INT | Late-night bets count | COUNT(*) FILTER (HOUR(timestamp) BETWEEN 2 AND 6) | 18 |
| `abnormal_hours_pct` | DECIMAL(5,4) | Temporal drift metric | bets_2am_to_6am / total_bets | 0.40 |
| `baseline_abnormal_pct_90d` | DECIMAL(5,4) | Baseline late-night percentage | AVG(abnormal_hours_pct) OVER (90 days) | 0.05 |
| `last_bet_timestamp` | TIMESTAMP_NTZ | Most recent bet (for incremental) | MAX(bet_timestamp) | "2026-01-15 22:15:00" |
| `calculated_at` | TIMESTAMP_NTZ | Calculation timestamp | CURRENT_TIMESTAMP() | "2026-01-15 23:00:00" |

**Row Count**: ~10K active players

---

## PROD Layer (Marts)

### RG_RISK_SCORES

**Purpose**: Final composite risk scores for all players

**Grain**: One row per player

**Materialization**: Table (rebuilt daily)

**Sources**: All intermediate models + `STG_GAMALYZE_SCORES`

| Column | Data Type | Description | Formula | Example |
|--------|-----------|-------------|---------|---------|
| `player_id` | VARCHAR(50) | Unique player identifier | PK | "PLR_1234_MA" |
| `composite_risk_score` | DECIMAL(5,4) | Final weighted risk score (0-1) | Σ(component * weight) | 0.8234 |
| `risk_category` | VARCHAR(20) | Risk classification | CASE composite_risk_score | "HIGH" |
| `loss_chase_score` | DECIMAL(5,4) | Normalized loss-chasing risk | normalize(bet_after_loss_ratio) | 0.8900 |
| `bet_escalation_score` | DECIMAL(5,4) | Normalized escalation risk | normalize(bet_escalation_ratio) | 0.9375 |
| `market_drift_score` | DECIMAL(5,4) | Composite drift risk | (horizontal + vertical + temporal) / 3 | 0.7500 |
| `temporal_risk_score` | DECIMAL(5,4) | DEPRECATED (use market_drift) | normalize(abnormal_hours_pct) | 0.7000 |
| `gamalyze_risk_score` | DECIMAL(5,4) | External neuro-marker composite | Σ(gamalyze_components * weights) | 0.7800 |
| `total_bets_7d` | INT | Total bets (7 days) | SUM(bets) | 45 |
| `total_wagered_7d` | DECIMAL(12,2) | Total amount wagered | SUM(bet_amount) | 2850.00 |
| `state_jurisdiction` | CHAR(2) | Player's home state | FROM stg_player_profiles | "MA" |
| `score_calculated_at` | TIMESTAMP_NTZ | When risk score was calculated | CURRENT_TIMESTAMP() | "2026-01-15 23:30:00" |
| `last_updated` | TIMESTAMP_NTZ | Last data refresh timestamp | MAX(source_timestamps) | "2026-01-15 23:30:00" |

**Component Weight Reference** (see `business_logic.md`):
````python
composite_risk_score = (
    (loss_chase_score * 0.30) +
    (bet_escalation_score * 0.25) +
    (market_drift_score * 0.15) +
    (temporal_risk_score * 0.10) +
    (gamalyze_risk_score * 0.20)
)
````

**Risk Category Thresholds**:
- CRITICAL: ≥0.80
- HIGH: 0.60-0.79
- MEDIUM: 0.40-0.59
- LOW: <0.40

**Row Count**: ~10K active players

---

### RG_AUDIT_TRAIL

**Purpose**: Comprehensive audit log for all risk flags and analyst decisions

**Grain**: One row per flag per analyst review

**Materialization**: Table (append-only)

| Column | Data Type | Description | Constraints | Example |
|--------|-----------|-------------|-------------|---------|
| `audit_id` | VARCHAR(50) | Unique audit record identifier | PK | "AUDIT_2026_001234" |
| `player_id` | VARCHAR(50) | Player being reviewed | FK → RG_RISK_SCORES | "PLR_1234_MA" |
| `composite_risk_score` | DECIMAL(5,4) | Risk score at time of review | NOT NULL | 0.8234 |
| `risk_category` | VARCHAR(20) | Risk classification | NOT NULL | "HIGH" |
| `analyst_id` | VARCHAR(50) | Analyst who reviewed case | NOT NULL for HIGH/CRITICAL | "ANALYST_042" |
| `analyst_action` | VARCHAR(50) | Decision made | IN ('approved', 'dismissed', 'escalated', 'timeout_applied') | "approved" |
| `analyst_notes` | VARCHAR(1000) | Rationale for decision | NOT NULL for HIGH/CRITICAL, >=10 chars | "Consistent loss-chasing pattern..." |
| `customer_notification_sent` | BOOLEAN | Whether customer was notified | NOT NULL | TRUE |
| `intervention_type` | VARCHAR(50) | Type of intervention | NULLABLE | "nudge", "timeout", "watchlist" |
| `state_jurisdiction` | CHAR(2) | State for compliance reporting | NOT NULL | "MA" |
| `score_calculated_at` | TIMESTAMP_NTZ | When risk score was generated | NOT NULL | "2026-01-15 23:30:00" |
| `analyst_reviewed_at` | TIMESTAMP_NTZ | When analyst reviewed | NOT NULL | "2026-01-16 09:15:00" |
| `review_duration_seconds` | INT | Time spent reviewing case | NULLABLE | 420 |
| `created_at` | TIMESTAMP_NTZ | Audit record creation | DEFAULT CURRENT_TIMESTAMP() | "2026-01-16 09:15:00" |

**Data Retention**: 7 years (regulatory requirement)

**Row Count**: ~50K records (growing daily)

---

## ANALYTICS Layer (Reporting)

### ANALYST_PERFORMANCE_METRICS

**Purpose**: Analyst productivity and decision quality tracking

**Grain**: One row per analyst per day

**Materialization**: View (refreshes from `RG_AUDIT_TRAIL`)

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `analyst_id` | VARCHAR(50) | Analyst identifier | "ANALYST_042" |
| `review_date` | DATE | Date of reviews | "2026-01-16" |
| `cases_reviewed` | INT | Total cases reviewed | 23 |
| `avg_review_time_seconds` | INT | Average time per case | 380 |
| `approval_rate` | DECIMAL(5,4) | % of cases approved | 0.7826 |
| `escalation_rate` | DECIMAL(5,4) | % of cases escalated | 0.0870 |
| `timeouts_applied` | INT | Timeouts applied count | 3 |
| `sla_compliance_rate` | DECIMAL(5,4) | % reviewed within SLA | 0.9565 |

**SLA Definitions**:
- CRITICAL: 2-hour review window
- HIGH: 24-hour review window

---

## Data Lineage
````
RAW.BET_TRANSACTIONS
    ↓
STAGING.STG_BET_LOGS
    ↓
PROD.INT_LOSS_CHASING_INDICATORS ──┐
PROD.INT_MARKET_DRIFT_DETECTION ───┤
                                    ├→ PROD.RG_RISK_SCORES
RAW.GAMALYZE_ASSESSMENTS           │      ↓
    ↓                               │   PROD.RG_AUDIT_TRAIL
STAGING.STG_GAMALYZE_SCORES ───────┘      ↓
                                    ANALYTICS.ANALYST_PERFORMANCE_METRICS
````

---

## Data Refresh Schedule

| Table | Refresh Frequency | Execution Time | Snowflake Task |
|-------|-------------------|----------------|----------------|
| `STG_*` | Real-time (view) | N/A | N/A |
| `INT_*` | Hourly | :05 past hour | `REFRESH_INT_MODELS` |
| `RG_RISK_SCORES` | Hourly | :30 past hour | `REFRESH_MARTS` |
| `RG_AUDIT_TRAIL` | Real-time (append) | N/A | N/A |
| `ANALYTICS.*` | Daily | 2:00 AM ET | `REFRESH_ANALYTICS` |

---

## Common Queries

### Get player's current risk profile
````sql
SELECT * FROM PROD.RG_RISK_SCORES
WHERE player_id = 'PLR_1234_MA';
````

### Get all HIGH/CRITICAL cases needing review
````sql
SELECT *
FROM PROD.RG_RISK_SCORES
WHERE risk_category IN ('HIGH', 'CRITICAL')
  AND player_id NOT IN (
      SELECT player_id FROM PROD.RG_AUDIT_TRAIL
      WHERE analyst_reviewed_at >= score_calculated_at
  )
ORDER BY composite_risk_score DESC;
````

### Player betting history (last 7 days)
````sql
SELECT *
FROM STAGING.STG_BET_LOGS
WHERE player_id = 'PLR_1234_MA'
  AND bet_timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY bet_timestamp DESC;
````

---

**For business logic and calculations, see**: `.claude/context/business_logic.md`
