"""Petits utilitaires : console colorée, JSON, dates."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Couleurs console (désactivables avec NO_COLOR) ───────────────────────────
import os

_COLOR = sys.stdout.isatty() and not os.getenv("NO_COLOR")


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def ok(msg: str) -> None:
    print(_c("32", "✔ ") + msg)


def info(msg: str) -> None:
    print(_c("36", "ℹ ") + msg)


def warn(msg: str) -> None:
    print(_c("33", "⚠ ") + msg)


def err(msg: str) -> None:
    print(_c("31", "✖ ") + msg, file=sys.stderr)


def step(msg: str) -> None:
    print(_c("35", "→ ") + msg)


# ── JSON ──────────────────────────────────────────────────────────────────────
def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stamp() -> str:
    """Horodatage compact local : 2026-08-29_1430"""
    return datetime.now().strftime("%Y-%m-%d_%H%M")


def fmt_money(value, currency: str = "EUR") -> str:
    """Formate un montant de façon lisible (gère les dicts {value, currency} de Chariow)."""
    if isinstance(value, dict):
        currency = value.get("currency", currency)
        value = value.get("value", value)
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    symbol = {"EUR": "€", "USD": "$", "GBP": "£", "XAF": "FCFA"}.get(currency.upper(), currency)
    return f"{num:,.2f} {symbol}".replace(",", " ")


def age_hours(path: Path) -> float:
    """Âge d'un fichier en heures (infini s'il n'existe pas)."""
    if not path.exists():
        return float("inf")
    age = datetime.now().timestamp() - path.stat().st_mtime
    return age / 3600.0


def truncate(text: str, limit: int = 30000) -> str:
    """Tronque un texte pour tenir dans le contexte du modèle."""
    if len(text) <= limit:
        return text
    suffix = f"\n… [tronqué : {len(text) - limit} caractères restants]"
    return text[: max(0, limit - len(suffix))] + suffix


def summarize_period(days: int = 30) -> str:
    """Description lisible de la période analysée (ex: 30 derniers jours)."""
    start = (datetime.now() - timedelta(days=days)).strftime("%d/%m/%Y")
    end = datetime.now().strftime("%d/%m/%Y")
    return f"{start} → {end}"
