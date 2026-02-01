from datetime import datetime
import pandas as pd
from .mappings import Mapping
from .db import SessionLocal
from .models import Fact

FORMS_FY = ("10-K","20-F","40-F")
FORMS_Q = ("10-Q",)

def _best_unit(units: list[str], priority: list[str]):
    for p in priority:
        if p in units:
            return p
    return units[0] if units else None

def _facts_for_tag(cik: int, taxonomy: str, tag: str):
    s = SessionLocal()
    try:
        q = (
            s.query(Fact)
            .filter(Fact.cik == cik, Fact.taxonomy == taxonomy, Fact.tag == tag)
        )
        return q.all()
    finally:
        s.close()

def _select_latest_per_end(rows):
    if not rows:
        return pd.DataFrame(columns=["end","val","filed","form","unit"])
    df = pd.DataFrame([{
        "end": r.end,
        "val": r.val,
        "filed": r.filed or datetime(1900,1,1),
        "form": r.form or "",
        "unit": r.unit,
    } for r in rows if r.val is not None and r.end is not None])
    if df.empty:
        return df
    df = df.sort_values(["end","filed"], ascending=[True, False])
    df = df.drop_duplicates(subset=["end"], keep="first")
    return df

def build_statement_history(cik: int, mapping: Mapping, period: str):
    forms = FORMS_FY if period == "FY" else FORMS_Q
    out = {}
    for line, refs in mapping.lines.items():
        collected = []
        for ref in refs:
            rows = _facts_for_tag(cik, ref.taxonomy, ref.tag)
            rows = [r for r in rows if (r.form in forms)]
            if not rows:
                continue
            df = _select_latest_per_end(rows)
            if df.empty:
                continue
            collected.append(df[["end","val","unit"]].rename(columns={"val": ref.tag, "unit": "unit"}))
        if not collected:
            continue
        merged = collected[0]
        for df in collected[1:]:
            merged = merged.merge(df, on=["end","unit"], how="outer")
        merged = merged.sort_values("end")
        merged[line] = merged[[c for c in merged.columns if c not in ("end","unit")]].bfill(axis=1).iloc[:,0]
        out[line] = merged[["end", line]].set_index("end")[line]
    if not out:
        return pd.DataFrame()
    result = pd.DataFrame(out).sort_index()
    return result

def compute_kpis(df_fy: pd.DataFrame, df_q: pd.DataFrame):
    k = {}
    if not df_q.empty and "revenue" in df_q.columns:
        ttm_rev = df_q["revenue"].dropna().tail(4).sum()
        k["ttm_revenue"] = float(ttm_rev) if pd.notna(ttm_rev) else None
    if not df_q.empty:
        if "operating_income" in df_q.columns:
            ttm_oi = df_q["operating_income"].dropna().tail(4).sum()
        else:
            ttm_oi = None
        da = df_q["da"].dropna().tail(4).sum() if "da" in df_q.columns else None
        if ttm_oi is not None and da is not None:
            k["ttm_ebitda"] = float(ttm_oi + da)
    return k
