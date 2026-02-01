set -euo pipefail

# 1) Write a never-crash marketdata provider
cat > src/edgar_model_builder/marketdata.py <<'PY'
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Quote:
    price: float | None
    market_cap: float | None
    currency: str | None

class MarketDataProvider:
    def quote(self, ticker: str) -> Quote:
        raise NotImplementedError

class NullProvider(MarketDataProvider):
    def quote(self, ticker: str) -> Quote:
        return Quote(price=None, market_cap=None, currency=None)

class YFinanceProvider(MarketDataProvider):
    def quote(self, ticker: str) -> Quote:
        # Hard-disable switch (for blocked networks)
        if os.getenv("EDGAR_DISABLE_YFINANCE", "0") == "1":
            return Quote(price=None, market_cap=None, currency=None)

        try:
            import yfinance as yf
            t = yf.Ticker(ticker)

            info = {}
            try:
                info = t.fast_info if hasattr(t, "fast_info") else {}
            except Exception:
                info = {}

            price = info.get("last_price") or info.get("lastPrice") or info.get("regularMarketPrice")
            mcap = info.get("market_cap") or info.get("marketCap")
            currency = info.get("currency") or info.get("currencySymbol")

            try:
                price = float(price) if price is not None else None
            except Exception:
                price = None

            try:
                mcap = float(mcap) if mcap is not None else None
            except Exception:
                mcap = None

            return Quote(price=price, market_cap=mcap, currency=currency)

        except Exception:
            # IMPORTANT: never crash build-pack because market data is optional
            return Quote(price=None, market_cap=None, currency=None)

def provider(name: str) -> MarketDataProvider:
    n = (name or "").lower().strip()
    if n in {"", "none", "null", "off", "disabled"}:
        return NullProvider()
    if n == "yfinance":
        return YFinanceProvider()
    raise ValueError(f"Unknown provider: {name}")
PY

# 2) Force default provider to none in settings.py (if that line exists)
python3 - <<'PY'
from pathlib import Path
p = Path("src/edgar_model_builder/settings.py")
s = p.read_text(encoding="utf-8")
s2 = s.replace('marketdata_provider: str = "yfinance"', 'marketdata_provider: str = "none"')
p.write_text(s2, encoding="utf-8")
print("Patched:", p)
PY

# 3) Ensure env forces provider OFF
touch .env
if grep -q '^MARKETDATA_PROVIDER=' .env; then
  sed -i '' 's/^MARKETDATA_PROVIDER=.*/MARKETDATA_PROVIDER=none/' .env
else
  echo 'MARKETDATA_PROVIDER=none' >> .env
fi

# 4) Verify: must not crash
poetry run python -c "from edgar_model_builder.marketdata import provider; print(provider('none').quote('AAPL'))"

echo "OK: marketdata disabled safely."
