"""Pipeline Kimagent : récupère les données → génère les livrables → écrit les fichiers.

Flux normal (mode automatique) :
    kimagent run <persona>
  1. charge les données de la boutique (cache local de moins de N heures,
     sinon appel au serveur MCP Chariow) ;
  2. pour chaque tâche du persona : demande au cerveau IA de produire le livrable ;
  3. écrit les livrables dans outputs/<persona>/<date>/ ;
  4. en mode sans cerveau (KIMAGENT_BRAIN=none) : écrit des fichiers de prompts
     prêts à copier dans Claude Desktop, ChatGPT, Cursor, etc.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from . import utils
from .brain import Brain, compact_context
from .chariow_mcp import fetch_store_data
from .config import DATA_DIR, OUTPUTS_DIR, Settings, ensure_dirs
from .demo_data import get_demo_data
from .ebook_engine import write_ebook
from .personas import Persona, Task, get_persona, list_personas

CACHE_FILE = DATA_DIR / "store_data.json"


# ── Chargement des données ────────────────────────────────────────────────────
def load_data(settings: Settings, force_fetch: bool = False, demo: bool = False) -> dict:
    """Charge les données : démo, cache récent, ou appel MCP réel."""
    if demo:
        utils.info("Mode démo : données fictives d'une boutique d'exemple.")
        return get_demo_data()

    age = utils.age_hours(CACHE_FILE)
    if not force_fetch and age < settings.data_max_age_hours:
        data = utils.read_json(CACHE_FILE)
        if data:
            utils.info(
                f"Données du cache local (il y a {age:.1f} h). "
                f"Utilisez `kimagent fetch --force` pour rafraîchir."
            )
            return data

    if force_fetch or age == float("inf"):
        utils.step("Connexion au serveur MCP Chariow…")
        data = asyncio.run(_fetch_real(settings))
        utils.write_json(CACHE_FILE, data)
        utils.ok("Données boutique enregistrées dans data/store_data.json")
        return data

    utils.warn("Le cache est trop ancien — données non actualisées.")
    return utils.read_json(CACHE_FILE) or get_demo_data()


async def _fetch_real(settings: Settings):
    from .oauth import auth_headers, authorize

    token = None
    try:
        token = authorize()
    except Exception as e:
        utils.warn(f"Connexion OAuth impossible : {e}")

    headers = auth_headers(token) if token else None
    try:
        return await fetch_store_data(settings, headers=headers)
    except Exception as e:
        utils.err(f"Échec de la récupération MCP : {e}")
        utils.info("Repli sur les données de démonstration. Relancez avec `--demo` si besoin.")
        return get_demo_data()


# ── Génération des livrables ──────────────────────────────────────────────────
def run_persona(
    persona: Persona,
    settings: Settings,
    demo: bool = False,
    force_fetch: bool = False,
    task_ids: list[str] | None = None,
    no_brain: bool = False,
) -> list[Path]:
    """Exécute les tâches d'un persona et écrit les livrables. Retourne les chemins."""
    ensure_dirs()
    data = load_data(settings, force_fetch=force_fetch, demo=demo)
    context = compact_context(data)

    tasks = [persona.task(t) for t in task_ids] if task_ids else persona.tasks
    date_dir = datetime.now().strftime("%Y-%m-%d")
    out_dir = OUTPUTS_DIR / persona.id / date_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    brain = None if no_brain else Brain(settings)
    brain_name = brain.provider if brain else "none"
    utils.step(f"Persona « {persona.name} » — cerveau IA : {brain_name}")
    utils.info(f"{len(tasks)} tâche(s) à produire dans {out_dir}")

    written: list[Path] = []
    for task in tasks:
        utils.step(f"Tâche : {task.title}")
        path = out_dir / task.output_file
        if task.special == "ebook_redaction" and brain is not None:
            # Rédaction longue : moteur dédié (chapitres par lots, contrôle longueur)
            manuscript = asyncio.run(
                write_ebook(brain, task.prompt, context, path, out_dir, data)
            )
            written.append(path)
            continue
        content = asyncio.run(_produce(brain, persona, task, context))
        path.write_text(content, encoding="utf-8")
        written.append(path)
        utils.ok(f"Écrit : {path.relative_to(OUTPUTS_DIR.parent)}")
    return written


async def _produce(brain: Brain | None, persona: Persona, task: Task, context: str) -> str:
    """Produit le contenu d'une tâche : via le cerveau, sinon un prompt prêt à copier."""
    header = (
        f"# {task.title}\n\n"
        f"**Persona** : {persona.name}  ·  **Généré par Kimagent** le "
        f"{datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n---\n\n"
    )
    if brain is not None:
        content = await brain.generate(
            system_prompt=persona.system_prompt,
            task_prompt=task.prompt,
            context=context,
        )
        if content:
            return header + content + "\n"
        utils.warn(f"Le cerveau n'a pas produit de contenu pour « {task.title} » — prompt écrit à la place.")

    # Mode prompt : fichier à copier-coller dans votre IA (Claude, ChatGPT, Cursor…)
    prompt_file = (
        f"--- PROMPT PRÊT À COPIER DANS VOTRE IA (Claude Desktop, ChatGPT, Cursor…) ---\n\n"
        f"> 1. Ouvrez votre outil IA connecté à Chariow (voir mcp/setup.md).\n"
        f"> 2. Copiez tout ce qui suit dans une nouvelle conversation.\n"
        f"> 3. Collez le résultat dans ce dossier quand c'est fait.\n\n"
        f"===== DÉBUT DU PROMPT =====\n\n"
        f"Tu es : {persona.name}.\n{persona.system_prompt}\n\n"
        f"Réalise la tâche suivante :\n{task.prompt}\n\n"
        f"Utilise les données de ma boutique Chariow (via le connecteur MCP) pour tout "
        f"chiffre cité. Données de référence :\n\n{utils.truncate(context, 8000)}\n\n"
        f"===== FIN DU PROMPT =====\n"
    )
    return header + prompt_file


# ── Rapport de synthèse ───────────────────────────────────────────────────────
def build_report(data: dict) -> str:
    """Résumé lisible de la boutique pour la commande `kimagent report`."""
    tools = data.get("tools", data)
    store = tools.get("get_store") or {}
    summary = store.get("sales_summary", {})
    analytics = tools.get("get_sales_analytics") or {}
    store_an = tools.get("get_store_analytics") or {}

    lines: list[str] = []
    lines.append(f"# Rapport boutique — {store.get('name', '?')}")
    lines.append("")
    lines.append(f"- **URL** : {store.get('url', '?')}")
    lines.append(f"- **Devise** : {store.get('currency', '?')}")
    lines.append(f"- **Ventes totales** : {summary.get('total_sales', '?')}")
    lines.append(f"- **Revenu total** : {utils.fmt_money(summary.get('total_revenue'))}")
    lines.append(f"- **Clients** : {summary.get('total_customers', '?')}")
    lines.append(f"- **Panier moyen** : {utils.fmt_money(summary.get('avg_order_value'))}")
    lines.append("")
    lines.append("## 30 derniers jours")
    lines.append("")
    lines.append(f"- Revenu : {utils.fmt_money(summary.get('last_30_days_revenue') or analytics.get('revenue'))}")
    lines.append(f"- Ventes : {summary.get('last_30_days_sales', analytics.get('sales_count', '?'))}")
    lines.append(f"- Visites : {store_an.get('visits', '?')}")
    lines.append(f"- Conversion : {store_an.get('conversion_rate', '?')}%")

    top = analytics.get("top_products") or []
    if top:
        lines.append("")
        lines.append("## Top produits")
        for p in top[:5]:
            lines.append(
                f"- {p.get('product', '?')} : {p.get('sales', '?')} ventes, "
                f"{utils.fmt_money(p.get('revenue'))}"
            )

    lines.append("")
    lines.append(f"*Source : {data.get('meta', {}).get('source', '?')} — "
                 f"extrait le {data.get('meta', {}).get('fetched_at', '?')}*")
    return "\n".join(lines)


def report(demo: bool = False, force_fetch: bool = False) -> str:
    settings = Settings()
    data = load_data(settings, force_fetch=force_fetch, demo=demo)
    return build_report(data)


def list_personas_table() -> str:
    lines = ["Personas disponibles :", ""]
    for p in list_personas():
        lines.append(f"  • {p.id:<12} — {p.name} : {p.tagline}")
        for t in p.tasks:
            lines.append(f"      · {t.id:<14} → {t.title}")
    return "\n".join(lines)
