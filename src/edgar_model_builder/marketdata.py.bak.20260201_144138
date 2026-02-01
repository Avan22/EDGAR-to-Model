from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class Quote:
    price: Optional[float] = None
    market_cap: Optional[float] = None
    currency: Optional[str] = None

    # Optional fundamentals (best effort)
    ev: Optional[float] = None
    ttm_revenue: Optional[float] = None
    ttm_ebitda: Optional[float] = None


class MarketDataProvider(Protocol):
    def quote(self, ticker: str) -> Quote: ...


class NullProvider:
    def quote(self, ticker: str) -> Quote:
        return Quote(price=None, market_cap=None, currency=None)


class YFinanceProvider:
    def quote(self, ticker: str) -> Quote:
        # Hard-disable switch
        if os.getenv("EDGAR_DISABLE_YFINANCE", "0") == "1":
            return Quote(price=None, market_cap=None, currency=None)

        try:
            import yfinance as yf  # type: ignore
        except Exception:
            return Quote(price=None, market_cap=None, currency=None)

        try:
            t = yf.Ticker(ticker)

            # ---- Fast path (usually works): fast_info ----
            fi = {}
            try:
                fi = getattr(t, "fast_info", {}) or {}
            except Exception:
                fi = {}

            price = (
                fi.get("last_price")
                or fi.get("lastPrice")
                or fi.get("regularMarketPrice")
                or fi.get("regular_market_price")
            )
            mcap = fi.get("market_cap") or fi.get("marketCap")
            currency = fi.get("currency") or fi.get("currencySymbol") or fi.get("currency_code")

            # Normalize types
            try:
                price = float(price) if price is not None else None
            except Exception:
                price = None

            try:
                mcap = float(mcap) if mcap is not None else None
            except Exception:
                mcap = None

            # ---- Fundamentals (best effort): t.info (can be slower / blocked) ----
            info = {}
            try:
                info = t.info if hasattr(t, "info") else {}
            except Exception:
                info = {}

            ev = info.get("enterpriseValue") or mcap
            ttm_revenue = info.get("totalRevenue")
            ttm_ebitda = info.get("ebitda")

            try:
                ev = float(ev) if ev is not None else None
            except Exception:
                ev = None

            try:
                ttm_revenue = float(ttm_revenue) if ttm_revenue is not None else None
            except Exception:
                ttm_revenue = None

            try:
                ttm_ebitda = float(ttm_ebitda) if ttm_ebitda is not None else None
            except Exception:
                ttm_ebitda = None

            return Quote(
                price=price,
                market_cap=mcap,
                currency=currency,
                ev=ev,
                ttm_revenue=ttm_revenue,
                ttm_ebitda=ttm_ebitda,
            )

        except Exception:
            # IMPORTANT: never crash builds because market data is optional
            return Quote(price=None, market_cap=None, currency=None)


def provider(name: str | None = None) -> MarketDataProvider:
    # Env override wins
    env_name = os.getenv("MARKETDATA_PROVIDER")
    chosen = (env_name if env_name is not None else name) or "yfinance"
    n = chosen.lower().strip()

    if n in {"", "none", "null", "off", "disabled"}:
        return NullProvider()
    if n in {"yfinance", "yf"}:
        return YFinanceProvider()

    raise ValueError(f"Unknown provider: {chosen}")
