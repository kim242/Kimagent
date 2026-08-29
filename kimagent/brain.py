"""Cerveau IA de Kimagent — génération de contenu via un fournisseur LLM.

Agnostique : fonctionne avec
  * Anthropic Claude  (ANTHROPIC_API_KEY)   → provider "anthropic"
  * OpenAI GPT        (OPENAI_API_KEY)       → provider "openai"
  * Ollama en local   (aucune clé requise)   → provider "ollama"
  * Aucun             → provider "none"      (Kimagent écrit alors les prompts
                                              prêts à copier dans votre IA)

Réglages dans le fichier .env (voir .env.example) :
  KIMAGENT_BRAIN=anthropic|openai|ollama|none
"""

from __future__ import annotations

import json
from typing import Optional

from .config import Settings
from .utils import err, truncate, warn

GUIDELINES = """\
Consignes de rédaction (à respecter strictement) :
- Rédige en français, sauf indication contraire explicite.
- Sois concret et actionnable : chaque recommandation doit être applicable aujourd'hui.
- Utilise les chiffres réels fournis dans le contexte (chiffre d'affaires, ventes, produits…).
- Cite les produits par leur nom exact tel qu'il apparaît dans les données.
- Ne jamais inventer de données, de prix ou de statistiques absents du contexte.
- Structure la réponse en Markdown propre, avec titres et listes à puces.
- Termine par une section "Prochaines actions (top 3)" listant les 3 actions
  les plus rentables à faire immédiatement, avec l'impact attendu estimé.
"""


class Brain:
    """Génère du contenu avec le fournisseur configuré. Retourne None si aucun."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def provider(self) -> str:
        return self.settings.brain_provider

    async def generate(
        self,
        system_prompt: str,
        task_prompt: str,
        context: str,
        max_tokens: int = 4000,
    ) -> Optional[str]:
        """Génère un contenu. Retourne None si aucun cerveau n'est configuré."""
        provider = self.settings.brain_provider
        user_prompt = (
            f"# TÂCHE À RÉALISER\n\n{task_prompt}\n\n"
            f"# DONNÉES DE LA BOUTIQUE (contexte réel)\n\n{truncate(context, self.settings.context_max_chars)}\n\n"
            f"{GUIDELINES}"
        )
        try:
            if provider == "anthropic":
                return await self._anthropic(system_prompt, user_prompt, max_tokens)
            if provider == "openai":
                return await self._openai(system_prompt, user_prompt, max_tokens)
            if provider == "ollama":
                return await self._ollama(system_prompt, user_prompt, max_tokens)
            if provider in ("none", ""):
                return None
            warn(f"Fournisseur IA inconnu : {provider!r} — mode 'none' utilisé.")
            return None
        except Exception as e:
            err(f"Le cerveau IA ({provider}) a échoué : {e}")
            err("Astuce : vérifiez votre clé API dans .env, ou passez en mode 'none' (KIMAGENT_BRAIN=none).")
            return None

    # ── Anthropic Claude ─────────────────────────────────────────────────────
    async def _anthropic(self, system: str, user: str, max_tokens: int) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        resp = await client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        ).strip()

    # ── OpenAI ───────────────────────────────────────────────────────────────
    async def _openai(self, system: str, user: str, max_tokens: int) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        resp = await client.chat.completions.create(
            model=self.settings.openai_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()

    # ── Ollama (local) ───────────────────────────────────────────────────────
    async def _ollama(self, system: str, user: str, max_tokens: int) -> str:
        import httpx

        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(f"{self.settings.ollama_url}/api/chat", json=payload)
            resp.raise_for_status()
            return (resp.json().get("message", {}).get("content") or "").strip()


def compact_context(data: dict, max_chars: int = 30000) -> str:
    """Transforme les données brutes MCP en un contexte lisible par le LLM."""
    tools = data.get("tools", data)
    store = tools.get("get_store") or {}

    lines: list[str] = []
    lines.append("=== BOUTIQUE ===")
    lines.append(json.dumps(store, ensure_ascii=False, default=str))

    for key, label in (
        ("list_products", "PRODUITS"),
        ("list_customers", "CLIENTS"),
        ("list_sales", "VENTES"),
        ("list_discounts", "REMISES"),
        ("list_licenses", "LICENCES"),
        ("list_pulses", "WEBHOOKS (PULSES)"),
    ):
        value = tools.get(key)
        if value is None:
            continue
        lines.append(f"\n=== {label} ===")
        items = value.get("data", value) if isinstance(value, dict) else value
        lines.append(json.dumps(items, ensure_ascii=False, default=str))

    for key in (
        "get_store_analytics",
        "get_sales_analytics",
        "get_customer_analytics",
        "get_visits_analytics",
        "get_conversion_rate_analytics",
    ):
        if tools.get(key):
            lines.append(f"\n=== {key} ===")
            lines.append(json.dumps(tools[key], ensure_ascii=False, default=str))

    return truncate("\n".join(lines), max_chars)
