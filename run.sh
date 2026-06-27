#!/usr/bin/env bash
# DB_SCRATCH CLI wrapper.
#
# Usage:
#   ./run.sh                    # run demo
#   ./run.sh shell              # interactive SQL shell
#   ./run.sh init ./data/app.db
#   ./run.sh sql ./data/app.db "SELECT 1"
#   ./run.sh --help

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! python3 -c "import typer" 2>/dev/null; then
  echo "Installing dependencies..."
  python3 -m pip install -e ".[dev]"
fi

if [ "$#" -eq 0 ]; then
  set -- demo
elif [ "${1:-}" = "--fresh" ]; then
  set -- demo --fresh
elif [ "${1:-}" = "--test" ]; then
  set -- test
fi

exec python3 -m db_scratch "$@"
