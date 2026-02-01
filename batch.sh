#!/usr/bin/env bash
set -euo pipefail

# refresh SEC ticker map once
poetry run edgar sec sync-tickers

PEERS="MSFT,GOOG,AMZN,META"

for T in AAPL MSFT GOOG AMZN META NVDA TSLA; do
  echo "== $T =="
  rm -rf "artifacts/$T" || true
  if ! poetry run edgar build-pack "$T" --peers="$PEERS"; then
    echo "!! FAILED for $T (skipping)"
    continue
  fi
done

echo "Done."
