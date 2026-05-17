"""
Cloudflare Quick Tunnels (trycloudflare.com) Manager.

Startet pro Site einen `cloudflared tunnel --url http://localhost:<PORT>` Subprozess,
parst die zugewiesene *.trycloudflare.com URL aus dem Output und hält sie im Tunnel-State.

Quick Tunnels brauchen KEINEN Cloudflare-Account. Ideal für temporäres Kunden-Hosting.

Voraussetzung: `cloudflared` muss installiert + im PATH sein.
  macOS:  brew install cloudflared
  Linux:  https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
"""
from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Any

from . import storage

URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

# In-Memory: slug -> Popen
_procs: dict[str, subprocess.Popen] = {}
_lock = threading.Lock()


def cloudflared_available() -> bool:
    return shutil.which("cloudflared") is not None


def _backend_port() -> int:
    return int(os.getenv("BACKEND_PORT", "8002"))


def _read_url(proc: subprocess.Popen, timeout: float = 30.0) -> str | None:
    """Liest stderr/stdout bis trycloudflare-URL gefunden oder Timeout."""
    deadline = time.time() + timeout
    assert proc.stdout is not None
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                return None
            time.sleep(0.1)
            continue
        m = URL_RE.search(line)
        if m:
            return m.group(0)
    return None


def start_tunnel(slug: str) -> dict[str, Any]:
    """Startet einen Quick Tunnel für die angegebene Site und persistiert ihn."""
    if not cloudflared_available():
        raise RuntimeError(
            "cloudflared nicht gefunden. Installiere es: "
            "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
        )

    with _lock:
        existing = _procs.get(slug)
        if existing and existing.poll() is None:
            for t in storage.load("tunnels"):
                if t.get("slug") == slug:
                    return t

        # Wir tunneln den GESAMTEN Backend-Port – die Site ist via /sites/<slug> erreichbar.
        # Für eine "saubere" Kunden-URL nutzen wir später eine Subdomain-Logik im Reverse-Proxy.
        port = _backend_port()
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        _procs[slug] = proc

    url = _read_url(proc, timeout=45.0)
    if not url:
        try:
            proc.terminate()
        except Exception:
            pass
        raise RuntimeError("Konnte trycloudflare-URL nicht ermitteln. Läuft cloudflared korrekt?")

    public_url = f"{url}/sites/{slug}"
    tunnel = {
        "id": slug,
        "slug": slug,
        "pid": proc.pid,
        "tunnel_host": url,
        "public_url": public_url,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    storage.upsert("tunnels", tunnel)
    return tunnel


def stop_tunnel(slug: str) -> bool:
    with _lock:
        proc = _procs.pop(slug, None)
    if proc and proc.poll() is None:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    tunnels = [t for t in storage.load("tunnels") if t.get("slug") != slug]
    storage.save("tunnels", tunnels)
    return True


def list_tunnels() -> list[dict[str, Any]]:
    items = storage.load("tunnels")
    # Status aktualisieren
    for t in items:
        proc = _procs.get(t["slug"])
        t["status"] = "running" if proc and proc.poll() is None else "stopped"
    return items
