import pandas as pd
from .marketdata import MarketDataProvider
from .normalize import compute_kpis
from .marketdata import provider

def build_comps_table(target_ticker: str, peers: list[str], kpis_by_ticker: dict[str, dict], mkt: MarketDataProvider):
    rows = []
    for t in [target_ticker] + peers:
        q = mkt.quote(t)
        k = kpis_by_ticker.get(t, {})
        ttm_rev = k.get("ttm_revenue")
        ttm_ebitda = k.get("ttm_ebitda")

        # --- Fallback (best-effort): if EDGAR fundamentals are missing, pull from marketdata (yfinance) ---
        _sym = locals().get("ticker") or locals().get("t") or locals().get("symbol")
        if _sym and (ttm_rev is None or ttm_ebitda is None):
            try:
                _q = provider("yfinance").quote(_sym)
                if ttm_rev is None:
                    ttm_rev = getattr(_q, "ttm_revenue", None)
                if ttm_ebitda is None:
                    ttm_ebitda = getattr(_q, "ttm_ebitda", None)
                # If EV is missing, backfill from provider too
                if locals().get("ev", None) is None:
                    ev = getattr(_q, "ev", None)
            except Exception:
                pass
        # --- end fallback ---
        mcap = q.market_cap
        ev = None
        if mcap is not None:
            cash = k.get("cash")
            debt = k.get("total_debt")
            if cash is not None or debt is not None:
                ev = mcap + (debt or 0.0) - (cash or 0.0)
            else:
                ev = mcap
        ev_rev = (ev / ttm_rev) if (ev is not None and ttm_rev) else None
        ev_ebitda = (ev / ttm_ebitda) if (ev is not None and ttm_ebitda) else None
        rows.append({
            "ticker": t,
            "price": q.price,
            "market_cap": mcap,
            "ev": ev,
            "ttm_revenue": ttm_rev,
            "ttm_ebitda": ttm_ebitda,
            "EV/Revenue": ev_rev,
            "EV/EBITDA": ev_ebitda,
        })
    df = pd.DataFrame(rows)
    return df
