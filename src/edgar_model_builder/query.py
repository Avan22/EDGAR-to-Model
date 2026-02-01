from datetime import datetime
from sqlalchemy import select, desc
from .db import SessionLocal
from .models import Company, Fact

def get_company_by_ticker(ticker: str) -> Company | None:
    s = SessionLocal()
    try:
        q = select(Company).where(Company.ticker == ticker.upper())
        return s.execute(q).scalars().first()
    finally:
        s.close()

def latest_fact_for_period(cik: int, taxonomy: str, tag: str, unit: str, end: datetime, forms: tuple[str,...]):
    s = SessionLocal()
    try:
        q = (
            select(Fact)
            .where(
                Fact.cik == cik,
                Fact.taxonomy == taxonomy,
                Fact.tag == tag,
                Fact.unit == unit,
                Fact.end == end,
                Fact.form.in_(forms),
            )
            .order_by(desc(Fact.filed), desc(Fact.accn))
        )
        return s.execute(q).scalars().first()
    finally:
        s.close()

def list_period_ends(cik: int, forms: tuple[str,...]):
    s = SessionLocal()
    try:
        q = (
            select(Fact.end)
            .where(Fact.cik == cik, Fact.form.in_(forms))
            .distinct()
            .order_by(desc(Fact.end))
        )
        return [r[0] for r in s.execute(q).all()]
    finally:
        s.close()
