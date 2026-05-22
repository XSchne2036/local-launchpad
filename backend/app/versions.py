"""Versionierung & Diff für generierte Sites."""
from __future__ import annotations

import difflib
import json
from datetime import datetime, timezone

from . import storage


def snapshot_site(site: dict, reason: str = "regenerate") -> dict:
    """Speichert einen Snapshot (content + html) vor dem Überschreiben."""
    version = {
        "id": f"{site['slug']}-{int(datetime.now(timezone.utc).timestamp()*1000)}",
        "slug": site["slug"],
        "lead_id": site.get("lead_id"),
        "language": site.get("language"),
        "theme": site.get("theme"),
        "reason": reason,
        "content": site.get("content"),
        "html": site.get("html"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return storage.upsert("site_versions", version)


def list_versions(slug: str) -> list[dict]:
    versions = [v for v in storage.load("site_versions") if v.get("slug") == slug]
    return sorted(versions, key=lambda v: v.get("created_at", ""), reverse=True)


def get_version(version_id: str) -> dict | None:
    return next((v for v in storage.load("site_versions") if v.get("id") == version_id), None)


def diff_content(a: dict, b: dict) -> str:
    """Unified diff zwischen zwei content-Dicts als JSON-Text."""
    sa = json.dumps(a or {}, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    sb = json.dumps(b or {}, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    return "\n".join(difflib.unified_diff(sa, sb, fromfile="alt", tofile="neu", lineterm=""))


def diff_html(diff_text: str) -> str:
    """Rendert unified-diff als farbiges HTML."""
    lines = []
    for line in diff_text.splitlines() or ["(keine Unterschiede)"]:
        esc = (line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        if line.startswith("+++") or line.startswith("---"):
            cls = "diff-meta"
        elif line.startswith("@@"):
            cls = "diff-hunk"
        elif line.startswith("+"):
            cls = "diff-add"
        elif line.startswith("-"):
            cls = "diff-del"
        else:
            cls = "diff-ctx"
        lines.append(f'<span class="{cls}">{esc}</span>')
    return "\n".join(lines)
