"""Configuration centrale de Kimagent (chemins, variables d'environnement, réglages)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Racine du dépôt = parent du package kimagent/
REPO_ROOT = Path(__file__).resolve().parent.parent

# Chargement du fichier .env à la racine (clés API, réglages…)
load_dotenv(REPO_ROOT / ".env")

DATA_DIR = REPO_ROOT / "data"                 # cache des données boutique (JSON)
OUTPUTS_DIR = REPO_ROOT / "outputs"           # livrables générés par les agents
TOKEN_DIR = REPO_ROOT / ".chariow"            # jetons OAuth Chariow (ne JAMAIS committer)
PROMPTS_DIR = REPO_ROOT / "agents" / "personas"
DOCS_DIR = REPO_ROOT / "docs"
MCP_DIR = REPO_ROOT / "mcp"


@dataclass
class Settings:
    """Réglages chargés depuis l'environnement (avec valeurs par défaut)."""

    # ── Chariow ──────────────────────────────────────────────────────────────
    mcp_url: str = field(
        default_factory=lambda: os.getenv(
            "CHARIOW_MCP_URL", "https://mcp.chariow.com/public"
        )
    )
    api_url: str = field(
        default_factory=lambda: os.getenv("CHARIOW_API_URL", "https://api.chariow.com/v1")
    )
    api_key: str = field(default_factory=lambda: os.getenv("CHARIOW_API_KEY", ""))
    store_slug: str = field(default_factory=lambda: os.getenv("CHARIOW_STORE_SLUG", ""))

    # ── Cerveau IA (provider) ────────────────────────────────────────────────
    # Valeurs possibles : anthropic | openai | ollama | none
    brain_provider: str = field(
        default_factory=lambda: os.getenv("KIMAGENT_BRAIN", "none").strip().lower()
    )

    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    anthropic_model: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    )

    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o")
    )

    ollama_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434")
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5")
    )

    # ── Comportement ─────────────────────────────────────────────────────────
    data_max_age_hours: int = field(
        default_factory=lambda: int(os.getenv("KIMAGENT_DATA_MAX_AGE_H", "12"))
    )
    context_max_chars: int = field(
        default_factory=lambda: int(os.getenv("KIMAGENT_CONTEXT_MAX_CHARS", "30000"))
    )
    agent_name: str = field(default_factory=lambda: os.getenv("KIMAGENT_NAME", "Kimagent"))

    @property
    def brain_configured(self) -> bool:
        """True si le fournisseur choisi dispose d'une clé (ou est local)."""
        if self.brain_provider == "anthropic":
            return bool(self.anthropic_api_key)
        if self.brain_provider == "openai":
            return bool(self.openai_api_key)
        if self.brain_provider == "ollama":
            return True
        return False  # none ou inconnu


def get_settings() -> Settings:
    return Settings()


def ensure_dirs() -> None:
    """Crée les dossiers de travail s'ils n'existent pas."""
    for d in (DATA_DIR, OUTPUTS_DIR, TOKEN_DIR):
        d.mkdir(parents=True, exist_ok=True)
