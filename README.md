# EDGAR-to-Model Deal Analytics (Automated Comps + Model Builder)

Production-grade starter that:
- pulls SEC XBRL Company Facts (EDGAR) into a versioned database
- normalizes US-GAAP tags into standardized financial lines
- computes TTM KPIs + trading multiples
- generates an Excel model (historicals + driver projections + DCF + sensitivities)
- generates an analyst-pack PDF (overview, KPIs, comps, valuation + sensitivity heatmaps)
- exposes a CLI (single command to build an analyst pack per ticker)

This repo is designed to be **correct-by-default** with SEC fair-access compliance and explicit, testable configs.

---

## 0) Prereqs (Mac)

1. Install **Homebrew** (if you don't have it): open Terminal and run:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Install toolchain:
```bash
brew install git python@3.12 docker
```

3. Install Docker Desktop:
- Open Docker Desktop, complete setup, ensure it says “Docker is running”.

---

## 1) Get the code

```bash
git clone <YOUR_REPO_URL_HERE> edgar-model-builder
cd edgar-model-builder
```

---

## 2) Configure environment

Copy the example env file and edit it:

```bash
cp .env.example .env
```

Open `.env` and set:
- `SEC_USER_AGENT` (required by SEC): e.g. `Avaneendra Trivedi avaneendra@email.com`
- Optional: `MARKETDATA_PROVIDER=yfinance`

---

## 3) Start databases (Postgres + Redis)

```bash
docker compose up -d
```

---

## 4) Create Python environment (Poetry)

```bash
python3 -m pip install --upgrade pip
pip install poetry
poetry install
```

---

## 5) Initialize tables

```bash
poetry run edgar db init
```

---

## 6) Pull the official ticker ↔ CIK list

```bash
poetry run edgar sec sync-tickers
```

---

## 7) Build your first analyst pack

Example (single company, with peers):

```bash
poetry run edgar build-pack --ticker AAPL --peers MSFT,GOOGL,AMZN,META
```

Outputs:
- `artifacts/AAPL/pack.pdf`
- `artifacts/AAPL/model.xlsx`
- `artifacts/AAPL/data.json`

---

## 8) Build a universe (optional)

```bash
poetry run edgar universe ingest --tickers AAPL,MSFT,GOOGL,AMZN,META
```

---

## 9) Troubleshooting

- If SEC blocks you: lower `SEC_RPS` in `.env` (default is safe).
- If Company Facts lacks a line item: adjust `config/mappings/us_gaap.yml`.

---

## CLI commands

```bash
poetry run edgar --help
poetry run edgar build-pack --help
```

---

## Notes on correctness

- SEC fair access: this code enforces a request rate below the SEC threshold by default.
- SEC endpoints used: `company_tickers.json`, `companyfacts` (XBRL JSON).
