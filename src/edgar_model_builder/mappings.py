from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass(frozen=True)
class TagRef:
    taxonomy: str
    tag: str

@dataclass(frozen=True)
class Mapping:
    unit_priority: list[str]
    lines: dict[str, list[TagRef]]

def load_mapping(path: str | Path) -> Mapping:
    p = Path(path)
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    unit_priority = list(d.get("unit_priority", ["USD"]))
    lines = {}
    for line, refs in d["lines"].items():
        lines[line] = [TagRef(**r) for r in refs]
    return Mapping(unit_priority=unit_priority, lines=lines)
