
set -u

TICKER="AAPL"
PEERS=(MSFT GOOGL AMZN META)

echo "== Repo =="
pwd

echo "== Make sure we are NOT disabling marketdata =="

if [ -f .env ]; then
  sed -i '' '/^MARKETDATA_PROVIDER=/d' .env
  sed -i '' '/^EDGAR_DISABLE_YFINANCE=/d' .env
fi


export MARKETDATA_PROVIDER="yfinance"
export EDGAR_DISABLE_YFINANCE="0"

echo "== Quick provider sanity check (must show non-None rev/ebitda) =="
poetry run python - <<'PY'
from edgar_model_builder.marketdata import provider
p = provider("yfinance")
for t in ["AAPL","MSFT","GOOGL","AMZN","META"]:
    q = p.quote(t)
    print(t, "price=", q.price, "mcap=", q.market_cap, "ev=", getattr(q,"ev",None),
          "rev=", getattr(q,"ttm_revenue",None), "ebitda=", getattr(q,"ttm_ebitda",None))
PY

echo "== Clear old artifacts =="
rm -rf "artifacts/${TICKER}"

echo "== Build pack (try multiple peer syntaxes until one works) =="
set +e
PEERS_CSV="$(IFS=,; echo "${PEERS[*]}")"
OK=0


poetry run edgar build-pack "${TICKER}" --peers "${PEERS[@]}"
RC=$?
if [ $RC -eq 0 ]; then OK=1; fi


if [ $OK -eq 0 ]; then
  poetry run edgar build-pack "${TICKER}" --peers="${PEERS_CSV}"
  RC=$?
  if [ $RC -eq 0 ]; then OK=1; fi
fi


if [ $OK -eq 0 ]; then
  poetry run edgar build-pack "${TICKER}" --peers "${PEERS_CSV}"
  RC=$?
  if [ $RC -eq 0 ]; then OK=1; fi
fi

set -e 2>/dev/null || true

if [ $OK -ne 1 ]; then
  echo "ERROR: build-pack failed in all peer formats."
  echo "Show help so we can see the exact expected syntax:"
  poetry run edgar build-pack --help || true
  exit 1
fi

echo "== Verify output files exist =="
ls -la "artifacts/${TICKER}" || exit 1

echo "== Verify data.json actually contains rev/ebitda (must NOT be null) =="
poetry run python - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/AAPL/data.json")
d = json.loads(p.read_text())

bad = []
for c in d["comps"]:
    t = c["ticker"]
    rev = c.get("ttm_revenue")
    ebt = c.get("ttm_ebitda")
    ev  = c.get("ev")
    print(t, "ev=", ev, "rev=", rev, "ebitda=", ebt, "EV/Rev=", c.get("EV/Revenue"), "EV/EBITDA=", c.get("EV/EBITDA"))
    if rev is None or ebt is None:
        bad.append(t)

if bad:
    raise SystemExit(f"\nERROR: These tickers still have null rev/ebitda in data.json: {bad}\n"
                     f"That means the build-pack run is not using the provider you tested.")
print("\nOK: data.json has rev/ebitda.")
PY

echo "== Open outputs =="
open "artifacts/${TICKER}/pack.pdf"
open "artifacts/${TICKER}/model.xlsx"
open "artifacts/${TICKER}/data.json"

echo "DONE."
