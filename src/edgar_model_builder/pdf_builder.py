from pathlib import Path
import io
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def _chart_to_png_bytes(df: pd.DataFrame, x, y, title: str):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(df[x], df[y])
    ax.set_title(title)
    ax.tick_params(axis='x', rotation=45)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf

def build_pack_pdf(out_path: str | Path, ticker: str, kpis: dict, comps: pd.DataFrame):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=letter)
    w, h = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, h-72, f"Analyst Pack: {ticker}")
    c.setFont("Helvetica", 11)
    y = h - 110
    for k, v in kpis.items():
        c.drawString(72, y, f"{k}: {v}")
        y -= 14

    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y-10, "Trading Comps")
    y -= 30

    cols = list(comps.columns)
    show = cols[:8]
    table = comps[show].copy()
    table = table.round(3)
    c.setFont("Helvetica", 8)
    ty = y
    c.drawString(72, ty, " | ".join(show))
    ty -= 12
    for _, r in table.iterrows():
        c.drawString(72, ty, " | ".join(str(r[col]) for col in show))
        ty -= 10
        if ty < 72:
            c.showPage()
            ty = h - 72
            c.setFont("Helvetica", 8)

    c.showPage()
    c.save()
    return str(out_path)
