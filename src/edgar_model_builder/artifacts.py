from pathlib import Path
import json
from .settings import settings

def artifacts_root():
    p = Path(settings.artifacts_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_json(path: str | Path, data: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return str(path)
