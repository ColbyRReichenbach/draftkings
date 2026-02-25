#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_PATH="${1:-$ROOT_DIR/data/dk_sentinel.duckdb}"

cd "$ROOT_DIR"

python3 scripts/seed_demo_cases.py \
  --db-path "$DB_PATH" \
  --completed 20 \
  --in-progress 2 \
  --preferred-player-ids-path docs/case_reviews/LEGACY_CASE_IDS.json

python3 scripts/export_demo_json.py \
  --db-path "$DB_PATH" \
  --manifest-path docs/case_reviews/CASE_MANIFEST.json \
  --queue-cap 12

echo "Static demo artifacts rebuilt at frontend/public/demo"
