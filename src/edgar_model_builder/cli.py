import asyncio
from pathlib import Path
import typer
from rich.console import Console
from .settings import settings
from .db import init_db
from .sec_client import SecClient
from .ingest import upsert_company, ingest_companyfacts
from .query import get_company_by_ticker
from .mappings import load_mapping
from .normalize import build_statement_history, compute_kpis
from .marketdata import provider
from .comps import build_comps_table
from .excel_builder import build_model_xlsx
from .pdf_builder import build_pack_pdf
from .artifacts import artifacts_root, write_json

app = typer.Typer(add_completion=False)
console = Console()

db_app = typer.Typer()
sec_app = typer.Typer()
universe_app = typer.Typer()
app.add_typer(db_app, name="db")
app.add_typer(sec_app, name="sec")
app.add_typer(universe_app, name="universe")

@db_app.command("init")
def db_init():
    init_db()
    console.print("[green]DB initialized[/green]")

@sec_app.command("sync-tickers")
def sync_tickers():
    asyncio.run(_sync_tickers())

async def _sync_tickers():
    c = SecClient()
    try:
        data = await c.tickers()
        for _, row in data.items():
            upsert_company(int(row["cik_str"]), row["ticker"], row["title"])
        console.print(f"[green]Synced {len(data)} tickers[/green]")
    finally:
        await c.aclose()

@universe_app.command("ingest")
def universe_ingest(tickers: str):
    asyncio.run(_universe_ingest([t.strip().upper() for t in tickers.split(",") if t.strip()]))

async def _universe_ingest(tickers: list[str]):
    c = SecClient()
    try:
        for t in tickers:
            co = get_company_by_ticker(t)
            if not co:
                console.print(f"[red]Unknown ticker: {t} (sync tickers first)[/red]")
                continue
            cf = await c.companyfacts(co.cik)
            ingest_companyfacts(co.cik, cf)
            console.print(f"[green]Ingested companyfacts: {t}[/green]")
    finally:
        await c.aclose()

@app.command("build-pack")
def build_pack(ticker: str, peers: str = "", mapping_path: str = "config/mappings/us_gaap.yml"):
    asyncio.run(_build_pack(ticker.upper(), [p.strip().upper() for p in peers.split(",") if p.strip()], mapping_path))

async def _build_pack(ticker: str, peers: list[str], mapping_path: str):
    co = get_company_by_ticker(ticker)
    if not co:
        raise typer.BadParameter("Ticker not found. Run: edgar sec sync-tickers")
    c = SecClient()
    try:
        cf = await c.companyfacts(co.cik)
        ingest_companyfacts(co.cik, cf)
    finally:
        await c.aclose()

    mapping = load_mapping(mapping_path)
    hist_fy = build_statement_history(co.cik, mapping, "FY")
    hist_q = build_statement_history(co.cik, mapping, "Q")

    kpis = compute_kpis(hist_fy, hist_q)
    for col in ["cash","total_debt"]:
        if col in hist_q.columns and not hist_q[col].dropna().empty:
            kpis[col] = float(hist_q[col].dropna().iloc[-1])

    mkt = provider(settings.marketdata_provider)
    kpis_by_ticker = {ticker: kpis}
    for p in peers:
        pco = get_company_by_ticker(p)
        if pco:
            ph_fy = build_statement_history(pco.cik, mapping, "FY")
            ph_q = build_statement_history(pco.cik, mapping, "Q")
            pk = compute_kpis(ph_fy, ph_q)
            for col in ["cash","total_debt"]:
                if col in ph_q.columns and not ph_q[col].dropna().empty:
                    pk[col] = float(ph_q[col].dropna().iloc[-1])
            kpis_by_ticker[p] = pk

    comps = build_comps_table(ticker, peers, kpis_by_ticker, mkt)

    assumptions = {"WACC": 0.10, "Terminal_Growth": 0.03}
    art_root = artifacts_root() / ticker
    model_path = build_model_xlsx(art_root / "model.xlsx", ticker, hist_fy, hist_q, comps, assumptions)
    pdf_path = build_pack_pdf(art_root / "pack.pdf", ticker, kpis, comps)
    data_path = write_json(art_root / "data.json", {"ticker": ticker, "kpis": kpis, "comps": comps.to_dict(orient="records")})

    console.print("[green]Built artifacts[/green]")
    console.print(model_path)
    console.print(pdf_path)
    console.print(data_path)
