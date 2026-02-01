from sqlalchemy import String, Integer, DateTime, Float, UniqueConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .db import Base

class Company(Base):
    __tablename__ = "companies"
    cik: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)

class Fact(Base):
    __tablename__ = "facts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cik: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    taxonomy: Mapped[str] = mapped_column(String(32), nullable=False)
    tag: Mapped[str] = mapped_column(String(128), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    start: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    fy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fp: Mapped[str | None] = mapped_column(String(16), nullable=True)
    form: Mapped[str | None] = mapped_column(String(16), nullable=True)
    filed: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    accn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    frame: Mapped[str | None] = mapped_column(String(32), nullable=True)
    val: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("cik","taxonomy","tag","unit","end","accn", name="uq_fact_key"),
        Index("ix_fact_tag_end", "taxonomy", "tag", "end"),
    )
