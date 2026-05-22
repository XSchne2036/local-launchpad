"""SMTP E-Mail-Outreach an Leads. Templates pro Sprache, Tracking in storage."""
from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Any

from . import storage


class OutreachError(RuntimeError):
    pass


def smtp_config() -> dict[str, Any]:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587") or "587")
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    from_email = os.getenv("SMTP_FROM", user)
    from_name = os.getenv("SMTP_FROM_NAME", "LocalLift")
    secure = (os.getenv("SMTP_SECURE", "starttls") or "starttls").lower()  # starttls|ssl|none
    return {
        "host": host, "port": port, "user": user, "password": password,
        "from_email": from_email, "from_name": from_name, "secure": secure,
        "configured": bool(host and from_email),
    }


# ---------------- Templates ----------------

SUBJECTS = {
    "de": "Wir haben eine Webseite für {name} vorbereitet 🎁",
    "en": "We prepared a website for {name} 🎁",
    "id": "Kami menyiapkan website untuk {name} 🎁",
}

BODIES = {
    "de": """Hallo {name}-Team,

wir sind auf {name} aufmerksam geworden und haben eine moderne, mobile-optimierte Webseite für euch vorbereitet – kostenlos und unverbindlich zur Ansicht:

👉 {site_url}

Falls die Seite passt, könnt ihr sie über den Button „Diese Webseite übernehmen" mit einem Klick beanspruchen. Domain, Anpassungen und Hosting besprechen wir individuell.

Beste Grüße
Das LocalLift Team
{from_name}

—
Du möchtest keine weiteren E-Mails von uns? Antworte einfach mit „STOP".
""",
    "en": """Hi {name} team,

we noticed {name} and prepared a modern, mobile-optimized website for you – free, no strings attached:

👉 {site_url}

If you like it, claim it with one click via the "Claim this website" button. We'll discuss domain, customization and hosting individually.

Best,
The LocalLift Team
{from_name}

—
Don't want emails from us? Just reply "STOP".
""",
    "id": """Halo tim {name},

kami menemukan {name} dan menyiapkan website modern yang mobile-friendly untuk Anda – gratis, tanpa kewajiban:

👉 {site_url}

Jika cocok, klaim dengan satu klik melalui tombol "Klaim website ini". Domain, penyesuaian, dan hosting kita bahas secara individual.

Salam,
Tim LocalLift
{from_name}

—
Tidak ingin email dari kami? Balas dengan "STOP".
""",
}


def render_template(lang: str, lead: dict, site_url: str, from_name: str) -> tuple[str, str]:
    lang = lang if lang in SUBJECTS else "de"
    name = lead.get("name") or "euer Unternehmen"
    subj = SUBJECTS[lang].format(name=name)
    body = BODIES[lang].format(name=name, site_url=site_url, from_name=from_name)
    return subj, body


# ---------------- Send ----------------

def send_email(to_email: str, subject: str, body: str, cfg: dict | None = None) -> dict:
    cfg = cfg or smtp_config()
    if not cfg["configured"]:
        raise OutreachError("SMTP nicht konfiguriert. Setze SMTP_HOST, SMTP_FROM (und SMTP_USER/SMTP_PASS).")

    msg = EmailMessage()
    msg["From"] = formataddr((cfg["from_name"], cfg["from_email"]))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid()
    msg.set_content(body)

    try:
        if cfg["secure"] == "ssl":
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ctx, timeout=20) as s:
                if cfg["user"]:
                    s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as s:
                s.ehlo()
                if cfg["secure"] == "starttls":
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                if cfg["user"]:
                    s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
    except Exception as e:
        raise OutreachError(f"SMTP-Fehler: {e}") from e

    return {"message_id": msg["Message-ID"], "to": to_email, "subject": subject}


def log_outreach(record: dict) -> dict:
    record = {
        **record,
        "id": record.get("id") or f"out-{int(datetime.now(timezone.utc).timestamp()*1000)}",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    return storage.upsert("outreach", record)
