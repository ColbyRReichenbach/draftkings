"""
DK Sentinel - DuckDB Data Loader

Loads generated CSV files into DuckDB for local development.
This provides a fast, embedded analytics database for testing dbt models
before migrating to Snowflake.

Usage:
    python scripts/load_to_duckdb.py

Output:
    - Creates data/dk_sentinel.duckdb
    - Loads 3 tables into raw schema:
      * raw.player_accounts (from players.csv)
      * raw.bet_transactions (from bets.csv)
      * raw.gamalyze_assessments (from gamalyze_scores.csv)
"""

import duckdb
from pathlib import Path
import sys


def check_csv_files():
    """Check if required CSV files exist."""
    required_files = [
        'data/players.csv',
        'data/bets.csv',
        'data/gamalyze_scores.csv'
    ]

    missing = []
    for filepath in required_files:
        if not Path(filepath).exists():
            missing.append(filepath)

    if missing:
        print("❌ Error: Required CSV files not found:")
        for filepath in missing:
            print(f"   - {filepath}")
        print("\nPlease run data generation first:")
        print("   python -m data_generation --n-players 10000")
        sys.exit(1)

    return required_files


def create_schemas(conn):
    """Create database schemas."""
    print("\n[2/4] Creating schemas...")

    schemas = ['raw', 'staging', 'prod', 'analytics']

    for schema in schemas:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        print(f"✓ Created schema: {schema}")


def load_csv_files(conn, csv_files):
    """Load CSV files into DuckDB tables using read_csv_auto."""
    print("\n[3/4] Loading CSV files...")

    # Mapping of CSV files to table names
    table_mapping = {
        'data/players.csv': 'raw.player_accounts',
        'data/bets.csv': 'raw.bet_transactions',
        'data/gamalyze_scores.csv': 'raw.gamalyze_assessments'
    }

    row_counts = {}

    for csv_file, table_name in table_mapping.items():
        print(f"  Loading {csv_file} → {table_name}")

        # Use DuckDB's read_csv_auto for automatic type inference
        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_csv_auto('{csv_file}', header=true)
        """)

        # Get row count
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        row_counts[table_name] = count

        print(f"✓ Loaded {table_name}: {count:,} rows")

    return row_counts


def show_verification(conn, row_counts):
    """Show verification information and sample data."""
    print("\n[4/4] Verification...")

    # Sample data from player_accounts
    print("\nSample from raw.player_accounts:")
    sample = conn.execute("SELECT * FROM raw.player_accounts LIMIT 3").df()
    print(sample.to_string(index=False))

    # Database statistics
    print("\nDatabase statistics:")
    print(f"  Total tables: {len(row_counts)}")
    total_rows = sum(row_counts.values())
    print(f"  Total rows: {total_rows:,}")

    # Database file size
    db_path = Path('data/dk_sentinel.duckdb')
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"  Database size: {size_mb:.1f} MB")


def main():
    """Main execution function."""
    print("=" * 70)
    print("DK SENTINEL - DuckDB Data Loader")
    print("=" * 70)

    print("\nConfiguration:")
    print("  DuckDB file: data/dk_sentinel.duckdb")
    print("  CSV directory: data/")

    # Step 1: Check CSV files
    csv_files = check_csv_files()

    # Step 2: Connect to DuckDB
    print("\n[1/4] Connecting to DuckDB...")
    db_path = 'data/dk_sentinel.duckdb'

    # Check if database already exists
    db_exists = Path(db_path).exists()

    conn = duckdb.connect(db_path)

    if db_exists:
        print(f"✓ Connected (existing database)")
    else:
        print(f"✓ Connected (new database created)")

    try:
        # Step 3: Create schemas
        create_schemas(conn)

        # Step 4: Load CSV files
        row_counts = load_csv_files(conn, csv_files)

        # Step 5: Verification
        show_verification(conn, row_counts)

        print("\n" + "=" * 70)
        print("✅ Data loading complete!")
        print("=" * 70)

        print("\nNext steps:")
        print("  1. Test connection: python -c \"import duckdb; duckdb.connect('data/dk_sentinel.duckdb')\"")
        print("  2. Configure dbt: cd dbt_project && dbt debug")
        print("  3. Run dbt models: dbt run --target dev")

    except Exception as e:
        print(f"\n❌ Error during loading: {e}")
        sys.exit(1)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
