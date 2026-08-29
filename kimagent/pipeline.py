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
import csv
from datetime import datetime
from math import ceil
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


# ── Tableau de bord objectif de CA (30 jours) ────────────────────────────────
def objectif_dashboard(data: dict, target_xaf: int | None = None) -> str:
    """Calcule l'écart entre le CA 30 jours et l'objectif (en FCFA). Purement local."""
    settings = Settings()
    target = target_xaf or settings.sales_target_xaf

    tools = data.get("tools", data)
    store = tools.get("get_store") or {}
    summary = store.get("sales_summary", {})
    an = tools.get("get_store_analytics") or {}
    sa = tools.get("get_sales_analytics") or {}

    rev30 = summary.get("last_30_days_revenue") or sa.get("revenue") or {}
    rev_xaf = utils.to_xaf(rev30, settings.store_default_currency)
    aov_xaf = utils.to_xaf(summary.get("avg_order_value"), settings.store_default_currency)
    conv = float(an.get("conversion_rate") or 0)
    visits = int(an.get("visits") or 0)

    gap = max(0.0, target - rev_xaf)
    progress = (rev_xaf / target * 100) if target else 0.0
    achieved = rev_xaf >= target

    sales_needed = ceil(gap / aov_xaf) if (gap > 0 and aov_xaf > 0) else 0
    visits_needed = ceil(sales_needed / (conv / 100)) if (sales_needed > 0 and conv > 0) else 0

    lines: list[str] = []
    lines.append(f"# 🎯 Objectif : {utils.fmt_xaf(target)} / 30 jours")
    lines.append("")
    lines.append(f"Boutique : **{store.get('name', '?')}**")
    lines.append("")
    lines.append("## Situation actuelle (30 derniers jours)")
    lines.append("")
    lines.append(f"- Revenu 30 j : **{utils.fmt_xaf(rev_xaf)}**")
    lines.append(f"- Progression : **{progress:.0f} %** de l'objectif")
    lines.append(f"- Panier moyen : {utils.fmt_xaf(aov_xaf)}")
    lines.append(f"- Visites : {visits:,}".replace(",", " "))
    lines.append(f"- Taux de conversion : {conv:.2f} %")

    lines.append("")
    if achieved:
        lines.append(f"## ✅ Objectif ATTEINT ({progress:.0f} %)")
        lines.append("")
        lines.append(f"- Excédent : {utils.fmt_xaf(rev_xaf - target)}")
        next_target = int(rev_xaf * 1.5)
        lines.append(
            f"- Suggestion : visez le prochain palier {utils.fmt_xaf(next_target)} "
            f"(KIMAGENT_OBJECTIF_XAF={next_target} dans .env)."
        )
    else:
        lines.append(f"## ⏳ Écart restant : {utils.fmt_xaf(gap)}")
        lines.append("")
        lines.append(f"- Ventes nécessaires : **{sales_needed:,}**".replace(",", " "))
        lines.append(f"  (panier moyen {utils.fmt_xaf(aov_xaf)})")
        if visits_needed:
            lines.append(f"- Visites nécessaires : **{visits_needed:,}**".replace(",", " "))
            lines.append(f"  (conversion actuelle {conv:.2f} %)")
        per_day = ceil(sales_needed / 30)
        plural = "" if per_day == 1 else "s"
        lines.append(f"- Rythme requis : **{per_day} vente{plural} / jour** "
                     f"≈ {utils.fmt_xaf(gap / 30)} / jour")
        lines.append("")
        lines.append("## Répartition par produit (suggestion)")
        top = sa.get("top_products") or []
        if top:
            total_top = sum(float(p.get("revenue") or 0) for p in top)
            for p in top[:5]:
                share = (float(p.get("revenue") or 0) / total_top * 100) if total_top else 0
                target_prod = gap * share / 100
                lines.append(
                    f"- {p.get('product', '?')} : viser {utils.fmt_xaf(target_prod)} "
                    f"({share:.0f} % de l'effort)"
                )
        lines.append("")
        lines.append("> Actions : `kimagent run objectif --tasks plan` pour le plan de "
                     "vente 30 jours, puis suivez ce tableau de bord chaque jour.")

    lines.append("")
    lines.append(f"*Source : {data.get('meta', {}).get('source', '?')} — "
                 f"extrait le {data.get('meta', {}).get('fetched_at', '?')}*")
    return "\n".join(lines)


def export_customers_csv(data: dict, path: Path) -> Path:
    """Exporte la liste des clients segmentée (VIP, inactifs, affiliés…) en CSV.

    Utile pour la prospection : importez ce fichier dans votre outil d'emailing
    ou de messagerie (WhatsApp Business, Brevo, Mailchimp…).
    """
    tools = data.get("tools", data)
    customers = (tools.get("list_customers") or {}).get("data", [])
    if not customers:
        raise ValueError("Aucun client dans les données — lancez `kimagent fetch` d'abord.")

    today = datetime.now().date()
    rows = []
    for c in customers:
        spent = utils.to_xaf(c.get("total_spent"), Settings().store_default_currency)
        last_order = c.get("last_order") or ""
        try:
            days_inactive = (today - datetime.strptime(last_order[:10], "%Y-%m-%d").date()).days
        except Exception:
            days_inactive = 0
        orders = int(c.get("orders_count") or 0)

        if c.get("is_affiliate"):
            segment = "affilie"
        elif spent >= 100 * 655.957 or orders >= 5:  # ≈ 100 € ou 5+ commandes
            segment = "vip"
        elif days_inactive >= 60:
            segment = "inactif_60j"
        else:
            segment = "actif_recent"

        rows.append({
            "nom": c.get("name", ""),
            "email": c.get("email", ""),
            "pays": c.get("country", ""),
            "segment": segment,
            "total_depense_fcfa": round(spent),
            "commandes": orders,
            "derniere_commande": last_order,
        })

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def list_personas_table() -> str:
    lines = ["Personas disponibles :", ""]
    for p in list_personas():
        lines.append(f"  • {p.id:<12} — {p.name} : {p.tagline}")
        for t in p.tasks:
            lines.append(f"      · {t.id:<14} → {t.title}")
    return "\n".join(lines)
