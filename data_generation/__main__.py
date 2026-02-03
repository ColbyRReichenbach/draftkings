"""
DK Sentinel Data Generation CLI

Orchestrates the entire data generation pipeline:
1. Generate players with latent factors
2. Generate Gamalyze scores
3. Generate bets with state machine
4. Inject edge cases
5. Run validation
6. Export CSVs

Usage:
    python -m data_generation --output-dir data/ --validate
"""

import click
import pandas as pd
import numpy as np
from pathlib import Path
import time
from .config import TOTAL_PLAYERS, RANDOM_SEED
from .player_generator import (
    generate_players,
    export_players_csv,
    validate_player_generation
)
from .gamalyze_generator import (
    generate_gamalyze_scores,
    export_gamalyze_csv,
    validate_gamalyze_scores
)
from .bet_generator import (
    generate_bets_for_all_players,
    export_bets_csv,
    validate_bet_generation
)
from .edge_cases import inject_edge_cases
from .validation import validate_all


@click.command()
@click.option('--output-dir', default='data/', help='Output directory for CSVs')
@click.option('--n-players', default=TOTAL_PLAYERS, help='Number of players to generate')
@click.option('--validate/--no-validate', default=True, help='Run statistical validation')
@click.option('--seed', default=RANDOM_SEED, help='Random seed for reproducibility')
def main(output_dir, n_players, validate, seed):
    """
    DK Sentinel Synthetic Data Generator

    Generates players.csv, bets.csv, gamalyze_scores.csv with realistic
    responsible gambling patterns for portfolio demonstration.
    """
    print("=" * 70)
    print("DK SENTINEL DATA GENERATION PIPELINE")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Players: {n_players:,}")
    print(f"  Output: {output_dir}")
    print(f"  Validation: {'Enabled' if validate else 'Disabled'}")
    print(f"  Random seed: {seed}")
    print()

    # Set global random seed
    np.random.seed(seed)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # =========================================================================
    # STEP 1: Generate Players
    # =========================================================================
    print("[1/6] Generating player cohorts...")
    start_time = time.time()

    players_df = generate_players(n_players)

    elapsed = time.time() - start_time
    print(f"✓ Completed in {elapsed:.1f}s\n")

    # =========================================================================
    # STEP 2: Generate Gamalyze Scores
    # =========================================================================
    print("[2/6] Generating Gamalyze assessments...")
    start_time = time.time()

    gamalyze_df = generate_gamalyze_scores(players_df)

    elapsed = time.time() - start_time
    print(f"✓ Completed in {elapsed:.1f}s\n")

    # =========================================================================
    # STEP 3: Generate Bets
    # =========================================================================
    print("[3/6] Generating betting sequences...")
    print("      (This may take 2-5 minutes for 10K players)\n")
    start_time = time.time()

    bets_df = generate_bets_for_all_players(players_df)

    elapsed = time.time() - start_time
    print(f"\n✓ Completed in {elapsed:.1f}s ({elapsed/60:.1f} minutes)\n")

    # =========================================================================
    # STEP 4: Inject Edge Cases
    # =========================================================================
    print("[4/6] Injecting edge cases...")
    start_time = time.time()

    players_df, bets_df, gamalyze_df = inject_edge_cases(
        players_df, bets_df, gamalyze_df
    )

    elapsed = time.time() - start_time
    print(f"✓ Completed in {elapsed:.1f}s\n")

    # =========================================================================
    # STEP 5: Validation
    # =========================================================================
    if validate:
        print("[5/6] Running statistical validation...")
        start_time = time.time()

        validation_results = validate_all(players_df, bets_df, gamalyze_df)

        elapsed = time.time() - start_time
        print(f"\n✓ Validation completed in {elapsed:.1f}s\n")

        # Check if all tests passed
        all_passed = all(validation_results.values())
        if not all_passed:
            click.echo("\n⚠ WARNING: Some validation tests failed.")
            click.echo("   Review output above for details.\n")
    else:
        print("[5/6] Skipping validation (--no-validate)\n")

    # =========================================================================
    # STEP 6: Export CSVs
    # =========================================================================
    print("[6/6] Exporting CSV files...")
    start_time = time.time()

    # Export players (without latent factors)
    players_export_path = output_path / 'players.csv'
    export_players_csv(players_df, str(players_export_path))

    # Export bets
    bets_export_path = output_path / 'bets.csv'
    export_bets_csv(bets_df, str(bets_export_path))

    # Export Gamalyze
    gamalyze_export_path = output_path / 'gamalyze_scores.csv'
    export_gamalyze_csv(gamalyze_df, str(gamalyze_export_path))

    elapsed = time.time() - start_time
    print(f"\n✓ Export completed in {elapsed:.1f}s")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nGenerated Files:")
    print(f"  📄 {players_export_path.absolute()}")
    print(f"     {len(players_df):,} players")
    print(f"  📄 {bets_export_path.absolute()}")
    print(f"     {len(bets_df):,} bets")
    print(f"  📄 {gamalyze_export_path.absolute()}")
    print(f"     {len(gamalyze_df):,} assessments")

    # File sizes
    try:
        players_size = players_export_path.stat().st_size / (1024 * 1024)
        bets_size = bets_export_path.stat().st_size / (1024 * 1024)
        gamalyze_size = gamalyze_export_path.stat().st_size / (1024 * 1024)
        total_size = players_size + bets_size + gamalyze_size

        print(f"\nFile Sizes:")
        print(f"  players.csv: {players_size:.2f} MB")
        print(f"  bets.csv: {bets_size:.2f} MB")
        print(f"  gamalyze_scores.csv: {gamalyze_size:.2f} MB")
        print(f"  Total: {total_size:.2f} MB")
    except:
        pass

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("  1. Review generated CSVs in", output_path.absolute())
    print("  2. Load into Snowflake: COPY INTO commands")
    print("  3. Run dbt pipeline: dbt run")
    print("  4. Validate dbt tests: dbt test")
    print("=" * 70)

    if validate and all_passed:
        print("\n✅ All validation tests passed!")
        print("   Data is ready for the dbt pipeline.\n")


if __name__ == '__main__':
    main()
