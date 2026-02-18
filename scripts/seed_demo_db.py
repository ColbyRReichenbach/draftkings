"""
Seed a demo DuckDB with realistic RG data for portfolio hosting.

Creates:
  - staging_staging.stg_player_profiles
  - staging_staging.stg_bet_logs
  - staging_staging.stg_gamalyze_scores
  - staging_prod.rg_risk_scores
  - staging_prod.rg_intervention_queue

Usage:
  python scripts/seed_demo_db.py --players 400
"""

from __future__ import annotations

import argparse
import os
import random
from datetime import datetime, timedelta, date

import duckdb


STATES = ["NJ", "MA", "PA"]
SPORTS = ["NFL", "NBA", "NHL", "MLB", "SOCCER", "UFC", "TENNIS"]
MARKETS = ["Moneyline", "Point Spread", "Totals", "Player Prop", "Parlay"]
MARKET_TIERS = [1.0, 0.7, 0.5, 0.2]
OUTCOMES = ["win", "loss", "push"]
GAMALYZE_VERSION = "v3.2.1"


def _score_range(category: str) -> tuple[float, float]:
    if category == "CRITICAL":
        return 0.85, 0.98
    if category == "HIGH":
        return 0.7, 0.88
    if category == "MEDIUM":
        return 0.45, 0.7
    return 0.1, 0.4


def _sample_score(category: str) -> float:
    low, high = _score_range(category)
    return round(random.uniform(low, high), 4)


def _derive_components(composite: float) -> dict[str, float]:
    # Spread components around the composite with small variance.
    def jitter():
        return max(0.0, min(1.0, composite + random.uniform(-0.12, 0.12)))

    return {
        "loss_chase_score": round(jitter(), 4),
        "bet_escalation_score": round(jitter(), 4),
        "market_drift_score": round(jitter(), 4),
        "temporal_risk_score": round(jitter(), 4),
        "gamalyze_risk_score": round(jitter(), 4),
    }


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _gamalyze_components(score: float) -> dict[str, int]:
    base = score * 100.0
    sensitivity_to_loss = _clamp(random.gauss(base + 6.0, 12.0))
    sensitivity_to_reward = _clamp(random.gauss(base, 12.0))
    risk_tolerance = _clamp(random.gauss(base, 12.0))
    decision_consistency = _clamp(random.gauss(100.0 - base, 12.0))
    return {
        "sensitivity_to_loss": int(round(sensitivity_to_loss)),
        "sensitivity_to_reward": int(round(sensitivity_to_reward)),
        "risk_tolerance": int(round(risk_tolerance)),
        "decision_consistency": int(round(decision_consistency)),
    }


def _gamalyze_score_from_components(components: dict[str, int]) -> float:
    return round(
        (components["sensitivity_to_loss"] / 100.0) * 0.40
        + (components["sensitivity_to_reward"] / 100.0) * 0.25
        + (components["risk_tolerance"] / 100.0) * 0.25
        + ((100 - components["decision_consistency"]) / 100.0) * 0.10,
        4,
    )


def _overall_risk_rating(score: float) -> str:
    if score >= 0.80:
        return "HIGH_RISK"
    if score >= 0.60:
        return "MODERATE_RISK"
    return "LOW_RISK"


def _primary_driver(components: dict[str, float]) -> str:
    return max(components.items(), key=lambda item: item[1])[0].replace("_", " ").title()


def _bets_per_player(category: str) -> int:
    if category == "CRITICAL":
        return random.randint(60, 90)
    if category == "HIGH":
        return random.randint(40, 70)
    if category == "MEDIUM":
        return random.randint(25, 45)
    return random.randint(8, 20)


def _bet_amount(category: str) -> float:
    base = {"CRITICAL": 180, "HIGH": 120, "MEDIUM": 60, "LOW": 25}[category]
    return round(max(5.0, random.gauss(base, base * 0.35)), 2)


def _odds() -> int:
    odds = random.choice([-140, -120, -110, +110, +125, +150, +180])
    return int(odds)


def _payout(bet_amount: float, odds_american: int, outcome: str) -> float:
    if outcome != "win":
        return 0.0
    if odds_american > 0:
        return round(bet_amount * (odds_american / 100.0), 2)
    return round(bet_amount * (100.0 / abs(odds_american)), 2)


def seed_demo_db(db_path: str, player_count: int) -> None:
    random.seed(42)

    # Ensure target directory exists (Render may not have /data yet).
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Risk mix: majority Critical/High/Medium, low fills remainder.
    mix = {
        "CRITICAL": int(player_count * 0.2),
        "HIGH": int(player_count * 0.35),
        "MEDIUM": int(player_count * 0.35),
    }
    mix["LOW"] = player_count - sum(mix.values())

    categories = []
    for category, count in mix.items():
        categories.extend([category] * count)
    random.shuffle(categories)

    now = datetime.utcnow()

    players = []
    risk_scores = []
    intervention_queue = []
    bets = []
    gamalyze_scores = []

    bet_id_counter = 1

    for idx in range(player_count):
        state = random.choice(STATES)
        player_id = f"PLR_{idx + 1:04d}_{state}"
        category = categories[idx]

        composite = _sample_score(category)
        components = _derive_components(composite)
        gamalyze_components = _gamalyze_components(components["gamalyze_risk_score"])
        components["gamalyze_risk_score"] = _gamalyze_score_from_components(gamalyze_components)
        assessment_date = date.today() - timedelta(days=random.randint(0, 30))
        calculated_at = now - timedelta(hours=random.randint(1, 72))

        players.append(
            (
                player_id,
                f"Player{idx + 1}",
                f"Demo{idx + 1}",
                f"player{idx + 1}@example.com",
                random.randint(21, 65),
                state,
                category.lower(),
                date.today() - timedelta(days=random.randint(200, 800)),
                False,
                None,
                "active",
                now,
            )
        )

        risk_scores.append(
            (
                player_id,
                components["loss_chase_score"],
                components["bet_escalation_score"],
                components["market_drift_score"],
                components["temporal_risk_score"],
                components["gamalyze_risk_score"],
                composite,
                category,
                calculated_at,
            )
        )

        intervention_queue.append(
            (
                player_id,
                composite,
                category,
                _primary_driver(components),
                components["loss_chase_score"],
                components["bet_escalation_score"],
                components["market_drift_score"],
                components["temporal_risk_score"],
                components["gamalyze_risk_score"],
                calculated_at,
            )
        )

        gamalyze_scores.append(
            (
                f"GMLY_{idx + 1:06d}",
                player_id,
                assessment_date,
                gamalyze_components["sensitivity_to_reward"],
                gamalyze_components["sensitivity_to_loss"],
                gamalyze_components["risk_tolerance"],
                gamalyze_components["decision_consistency"],
                _overall_risk_rating(components["gamalyze_risk_score"]),
                now,
                GAMALYZE_VERSION,
            )
        )

        bet_count = _bets_per_player(category)
        for seq in range(1, bet_count + 1):
            bet_amount = _bet_amount(category)
            odds = _odds()
            outcome = random.choice(OUTCOMES)
            bet_ts = now - timedelta(days=random.randint(0, 89), hours=random.randint(0, 23))
            bets.append(
                (
                    f"BET_{bet_id_counter:08d}",
                    player_id,
                    bet_ts,
                    random.choice(SPORTS),
                    random.choice(MARKETS),
                    bet_amount,
                    odds,
                    outcome,
                    _payout(bet_amount, odds, outcome),
                    random.choice(MARKET_TIERS),
                    state,
                    seq,
                    now,
                )
            )
            bet_id_counter += 1

    conn = duckdb.connect(db_path)
    conn.execute("CREATE SCHEMA IF NOT EXISTS staging_staging")
    conn.execute("CREATE SCHEMA IF NOT EXISTS staging_prod")

    def drop_object(qualified: str) -> None:
        try:
            conn.execute(f"DROP VIEW IF EXISTS {qualified}")
        except duckdb.CatalogException:
            pass
        try:
            conn.execute(f"DROP TABLE IF EXISTS {qualified}")
        except duckdb.CatalogException:
            pass

    drop_object("staging_staging.stg_player_profiles")
    conn.execute(
        """
        CREATE TABLE staging_staging.stg_player_profiles (
            player_id VARCHAR,
            first_name VARCHAR,
            last_name VARCHAR,
            email VARCHAR,
            age INTEGER,
            state_jurisdiction VARCHAR,
            risk_cohort VARCHAR,
            account_created_date DATE,
            self_excluded BOOLEAN,
            self_exclusion_history VARCHAR,
            account_status VARCHAR,
            updated_at TIMESTAMP
        )
        """
    )
    conn.executemany(
        "INSERT INTO staging_staging.stg_player_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        players,
    )

    drop_object("staging_staging.stg_bet_logs")
    conn.execute(
        """
        CREATE TABLE staging_staging.stg_bet_logs (
            bet_id VARCHAR,
            player_id VARCHAR,
            bet_timestamp TIMESTAMP,
            sport_category VARCHAR,
            market_type VARCHAR,
            bet_amount DOUBLE,
            odds_american INTEGER,
            outcome VARCHAR,
            payout_amount DOUBLE,
            market_tier DOUBLE,
            state_jurisdiction VARCHAR,
            bet_sequence_num INTEGER,
            loaded_at TIMESTAMP
        )
        """
    )
    conn.executemany(
        "INSERT INTO staging_staging.stg_bet_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        bets,
    )

    drop_object("staging_staging.stg_gamalyze_scores")
    conn.execute(
        """
        CREATE TABLE staging_staging.stg_gamalyze_scores (
            assessment_id VARCHAR,
            player_id VARCHAR,
            assessment_date DATE,
            sensitivity_to_reward INTEGER,
            sensitivity_to_loss INTEGER,
            risk_tolerance INTEGER,
            decision_consistency INTEGER,
            overall_risk_rating VARCHAR,
            loaded_at TIMESTAMP,
            gamalyze_version VARCHAR
        )
        """
    )
    conn.executemany(
        "INSERT INTO staging_staging.stg_gamalyze_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        gamalyze_scores,
    )

    drop_object("staging_prod.rg_risk_scores")
    conn.execute(
        """
        CREATE TABLE staging_prod.rg_risk_scores (
            player_id VARCHAR,
            loss_chase_score DOUBLE,
            bet_escalation_score DOUBLE,
            market_drift_score DOUBLE,
            temporal_risk_score DOUBLE,
            gamalyze_risk_score DOUBLE,
            composite_risk_score DOUBLE,
            risk_category VARCHAR,
            calculated_at TIMESTAMP
        )
        """
    )
    conn.executemany(
        "INSERT INTO staging_prod.rg_risk_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        risk_scores,
    )

    drop_object("staging_prod.rg_intervention_queue")
    conn.execute(
        """
        CREATE TABLE staging_prod.rg_intervention_queue (
            player_id VARCHAR,
            composite_risk_score DOUBLE,
            risk_category VARCHAR,
            primary_driver VARCHAR,
            loss_chase_score DOUBLE,
            bet_escalation_score DOUBLE,
            market_drift_score DOUBLE,
            temporal_risk_score DOUBLE,
            gamalyze_risk_score DOUBLE,
            calculated_at TIMESTAMP
        )
        """
    )
    conn.executemany(
        "INSERT INTO staging_prod.rg_intervention_queue VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        intervention_queue,
    )

    # Clear runtime queue so stale player IDs from prior seeds do not persist.
    try:
        conn.execute("DELETE FROM rg_queue_cases")
    except duckdb.CatalogException:
        pass

    conn.close()

    print(f"Seeded {player_count} players with majority critical/high/medium cases.")
    print(f"Database: {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo DuckDB data.")
    parser.add_argument("--players", type=int, default=400, help="Number of players to generate.")
    parser.add_argument("--db-path", type=str, default="data/dk_sentinel.duckdb")
    args = parser.parse_args()
    seed_demo_db(args.db_path, args.players)


if __name__ == "__main__":
    main()
