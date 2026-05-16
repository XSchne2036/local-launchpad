"""JSON-basierter Storage. Eine Datei pro 'Tabelle' im data/ Ordner."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

_locks: dict[str, threading.Lock] = {}


def _lock(name: str) -> threading.Lock:
    if name not in _locks:
        _locks[name] = threading.Lock()
    return _locks[name]


def _path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def load(name: str) -> list[dict[str, Any]]:
    p = _path(name)
    if not p.exists():
        return []
    with _lock(name):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []


def save(name: str, items: list[dict[str, Any]]) -> None:
    with _lock(name):
        _path(name).write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def upsert(name: str, item: dict[str, Any], key: str = "id") -> dict[str, Any]:
    """Insert oder Update anhand eines Keys (default: 'id'). Gibt das gespeicherte Item zurück."""
    items = load(name)
    for i, existing in enumerate(items):
        if existing.get(key) == item.get(key):
            items[i] = {**existing, **item}
            save(name, items)
            return items[i]
    items.append(item)
    save(name, items)
    return item
