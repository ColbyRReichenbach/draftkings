---
name: behavioral-analytics
description: Domain knowledge for responsible gaming pattern detection - use when working with risk scores, loss-chasing indicators, market drift, or Gamalyze neuro-markers
allowed-tools: Read
---

# Behavioral Analytics for Responsible Gaming

## When to Use This Skill
- Calculating risk scores or component weights
- Implementing loss-chasing detection logic
- Analyzing market drift patterns
- Interpreting Gamalyze neuro-marker assessments
- Setting behavioral thresholds

---

## Gamalyze Neuro-Markers (0-100 Scale)

**Integration Date**: January 2026 (Mindway AI partnership)

### Four Core Markers

**1. Sensitivity to Reward** (0-100)
- **What it measures**: Tendency to increase bet size after wins
- **Risky threshold**: >70
- **Interpretation**: "Hot hand" fallacy - belief that winning streak continues

**2. Sensitivity to Loss** (0-100) ⭐ **STRONGEST PREDICTOR**
- **What it measures**: Tendency to increase bet size after losses
- **Risky threshold**: >75
- **Interpretation**: Loss-chasing behavior - trying to "win it back"
- **Evidence**: r=0.72 correlation with bet_escalation_ratio

**3. Risk Tolerance** (0-100)
- **What it measures**: Preference for high-variance bets
- **Risky threshold**: >80
- **Interpretation**: Parlays, longshots, low-probability high-payout bets

**4. Decision Consistency** (0-100) ⚠️ **INVERSE SCORING**
- **What it measures**: Pattern predictability in betting behavior
- **Risky threshold**: <30 (lower = riskier)
- **Interpretation**: Erratic, impulsive decision-making

---

## Market Drift Typology

### Dimension 1: Horizontal Drift (Sport Diversity)

**Metric**: Number of unique sports bet on within 7-day window

**Baseline**: Player's typical sport count (rolling 90-day average)

**Risk Levels**:
- **Normal**: 1.2x baseline (e.g., NFL bettor tries NBA playoffs)
- **Moderate**: 2-3x baseline
- **Risky**: >3x baseline

**Interpretation**: "I'll bet on anything available" - desperation signal

**Example**:
```sql
-- Player normally bets 2 sports (NFL, NBA)
-- This week: NFL, NBA, MLB, NHL, Soccer, Table Tennis = 6 sports
-- Drift ratio: 6 / 2 = 3.0x → RISKY
```

---

### Dimension 2: Vertical Drift (Market Quality Tier)

**Tier Classification**:
```python
MARKET_TIERS = {
    1.0: ['NFL', 'NBA', 'MLB', 'NHL', 'SOCCER'],           # Pro leagues
    0.7: ['NCAA_BASKETBALL', 'NCAA_FOOTBALL'],             # College sports
    0.5: ['MMA', 'BOXING', 'TENNIS'],                      # Mid-tier
    0.2: ['TABLE_TENNIS', 'KOREAN_BASEBALL', 'ESPORTS']    # Niche/low-liquidity
}
```

**Metric**: Average market tier this week vs. baseline

**Risk Threshold**: Drop >50% (e.g., 1.0 → 0.5 or below)

**Rationale**: Low-liquidity markets = less informed betting = desperation

**Example**:
```sql
-- Player baseline: Tier 1.0 (NFL, NBA)
-- This week: Table Tennis (0.2), Korean Baseball (0.2)
-- New tier: 0.2
-- Drift: (1.0 - 0.2) / 1.0 = 80% drop → CRITICAL
```

---

### Dimension 3: Temporal Drift (Time-of-Day)

**Metric**: Percentage of bets placed during "abnormal hours" (2-6 AM)

**Baseline**: Player's typical betting time distribution

**Risk Threshold**: >30% of bets during abnormal hours when baseline is <5%

**Correlates With**:
- Alcohol consumption
- Insomnia from gambling stress
- Hiding behavior from spouse (betting while they sleep)

**Academic Source**: Auer & Griffiths (2022) "Temporal Patterns in Problem Gambling"

**Example**:
```sql
-- Player baseline: 90% of bets 6 PM - 11 PM (primetime sports)
-- This week: 40% of bets 2 AM - 5 AM
-- Temporal drift: 40% / 5% = 8x increase → HIGH RISK
```

---

## Loss-Chasing Detection

### Metric 1: Bet After Loss Ratio

**Formula**: `bets_after_loss / total_bets`

**Thresholds**:
- **<0.40**: Normal (winning/losing doesn't affect next bet)
- **0.40-0.60**: Moderate (some reactivity)
- **0.60-0.75**: High (clear loss-chasing pattern)
- **>0.75**: Critical (compulsive - almost every loss triggers next bet)

**Evidence**: 68% of self-excluded players in pilot study showed ratio >0.75

---

### Metric 2: Bet Escalation Ratio

**Formula**: `avg_bet_after_loss / avg_bet_after_win`

**Thresholds**:
- **<1.2**: Consistent bet sizing
- **1.2-1.5**: Moderate escalation
- **1.5-2.0**: High escalation (concerning)
- **>2.0**: Critical (doubling down after losses)

**Correlation**: r=0.72 with Gamalyze "Sensitivity to Loss"

---

## Risk Score Component Weights (v1.0)

**CRITICAL**: These weights are subject to **monthly active learning calibration** based on analyst feedback.
```python
COMPOSITE_RISK_WEIGHTS = {
    'loss_chase_score': 0.30,      # Bet after loss ratio
    'bet_escalation_score': 0.25,  # Bet size increase after losses
    'market_drift_score': 0.15,    # Sport/tier/time drift composite
    'temporal_risk_score': 0.10,   # Late-night betting patterns
    'gamalyze_risk_score': 0.20    # Mindway AI neuro-marker composite
}

# Weights MUST sum to 1.0 - enforced via dbt test
```

**Weight Selection Rationale**:
- **Loss chasing (0.30)**: Strongest empirical predictor (68% of self-excluded showed this)
- **Bet escalation (0.25)**: r=0.72 correlation with Gamalyze sensitivity to loss
- **Market drift (0.15)**: Moderate predictor; common in normal exploration behavior
- **Temporal (0.10)**: Highest variance; confounded by shift workers and time zones
- **Gamalyze (0.20)**: External validation baseline; r=0.58 correlation with composite features

---

## State-Specific Regulatory Thresholds

### Massachusetts (205 CMR 238.04)

**Abnormal Play Detection**:
```sql
-- Trigger: Bet amount >10x rolling 90-day average
SELECT player_id, bet_amount, rolling_avg
FROM current_bets
WHERE bet_amount > (rolling_avg_90d * 10)
```

**High Deposit After Loss**:
```sql
-- Trigger: Deposit >$5K within 24h after losses >$10K
SELECT player_id
FROM deposits
WHERE amount > 5000
  AND player_id IN (
      SELECT player_id 
      FROM losses_24h 
      WHERE total_losses > 10000
  )
```

**Required Action**: Internal documentation (no SAR unless additional criteria met)

---

### New Jersey

**Multi-Venue Pattern Monitoring**:
- Track cross-platform betting (DraftKings + FanDuel + BetMGM via state database)
- **Trigger**: 3+ high-risk flags in 30-day period across any platforms
- **Required Action**: Mandatory 24-hour timeout

---

### Pennsylvania

**Self-Exclusion Reversal Tracking**:
```sql
-- Trigger: 3+ self-exclusion reversals in 6-month window
SELECT player_id, COUNT(*) AS reversals
FROM self_exclusion_history
WHERE action = 'reversed'
  AND action_timestamp >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY player_id
HAVING COUNT(*) >= 3
```

**Required Action**: Mandatory Problem Gambling Council referral

---

## Common Analytical Mistakes

❌ **Absolute thresholds without context**
- Bad: "$500 bet = high risk"
- Good: "3x player's typical bet size = high risk"

❌ **Flagging all late-night betting**
- Bad: Any bet 2-6 AM = risky
- Good: Compare to player's baseline time-of-day pattern

❌ **Treating all sport exploration as drift**
- Bad: Trying NBA = horizontal drift
- Good: Distinguish horizontal (NFL→NBA) from vertical (NFL→Table Tennis)

❌ **Ignoring base rates**
- Bad: 80% loss-chase ratio = critical for all players
- Good: Account for players with only 5 total bets (insufficient data)
