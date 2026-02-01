from datetime import datetime
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal
from .models import Company, Fact

def upsert_company(cik: int, ticker: str, name: str):
    s = SessionLocal()
    try:
        c = s.get(Company, cik)
        if c is None:
            c = Company(cik=cik, ticker=ticker.upper(), name=name)
            s.add(c)
        else:
            c.ticker = ticker.upper()
            c.name = name
        s.commit()
    finally:
        s.close()

def parse_dt(x: str | None):
    if not x:
        return None
    return datetime.fromisoformat(x)

def ingest_companyfacts(cik: int, companyfacts: dict):
    s = SessionLocal()
    try:
        facts = companyfacts.get("facts", {})
        for taxonomy, tags in facts.items():
            for tag, payload in tags.items():
                units = payload.get("units", {})
                for unit, rows in units.items():
                    for r in rows:
                        val = r.get("val")
                        try:
                            f = Fact(
                                cik=cik,
                                taxonomy=taxonomy,
                                tag=tag,
                                unit=unit,
                                start=parse_dt(r.get("start")),
                                end=parse_dt(r["end"]),
                                fy=r.get("fy"),
                                fp=r.get("fp"),
                                form=r.get("form"),
                                filed=parse_dt(r.get("filed")),
                                accn=r.get("accn"),
                                frame=r.get("frame"),
                                val=float(val) if val is not None else None,
                            )
                            s.add(f)
                            s.flush()
                        except (IntegrityError, ValueError, TypeError):
                            s.rollback()
        s.commit()
    finally:
        s.close()
