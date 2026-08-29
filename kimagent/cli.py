"""Interface en ligne de commande de Kimagent.

Commandes :
  kimagent auth      → connecte votre compte Chariow (OAuth, une fois)
  kimagent fetch     → récupère les données de la boutique via MCP (cache local)
  kimagent run       → exécute un persona (génère les livrables)
  kimagent report    → rapport de synthèse de la boutique
  kimagent tools     → liste les outils MCP exposés par le serveur Chariow
  kimagent prompts   → affiche les prompts prêts à copier pour une tâche
  kimagent cron      → affiche la ligne crontab pour l'automatisation
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from . import utils
from .chariow_mcp import ChariowMCPError, list_mcp_tools
from .config import REPO_ROOT, Settings, ensure_dirs
from .personas import PERSONAS, get_persona, list_personas
from .pipeline import build_report, list_personas_table, load_data, run_persona

BANNER = r"""
 _  __ _                         _
| |/ /(_)_ __ ___   __ _  __ _  (_) ___
| ' / | | '_ ` _ \ / _` |/ _` | | |/ _ \
| . \ | | | | | | | (_| | (_| | | |  __/
|_|\_\|_|_| |_| |_|\__,_|\__, | |_|\___|
                          |___/   v1.0
Agent IA — boutique Chariow · https://mcp.chariow.com/public
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kimagent",
        description="Agent IA connecté à votre boutique Chariow via MCP.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("auth", help="Connecter votre compte Chariow (OAuth)")

    p_fetch = sub.add_parser("fetch", help="Récupérer les données de la boutique (MCP)")
    p_fetch.add_argument("--force", action="store_true", help="Ignorer le cache local")
    p_fetch.add_argument("--demo", action="store_true", help="Utiliser les données de démonstration")
    p_fetch.add_argument("--save", type=Path, default=None, help="Sauvegarder le JSON à cet endroit")

    p_run = sub.add_parser("run", help="Exécuter un persona (générer des livrables)")
    p_run.add_argument("persona", nargs="?", default=None,
                       help="Identifiant du persona (ex: marketing)")
    p_run.add_argument("--tasks", default=None,
                       help="Tâches à exécuter, séparées par des virgules (ex: posts,emails)")
    p_run.add_argument("--demo", action="store_true", help="Utiliser les données de démonstration")
    p_run.add_argument("--force", action="store_true", help="Forcer le rafraîchissement MCP")
    p_run.add_argument("--no-brain", action="store_true",
                       help="Écrire les prompts prêts à copier au lieu d'appeler le LLM")

    p_report = sub.add_parser("report", help="Rapport de synthèse de la boutique")
    p_report.add_argument("--demo", action="store_true", help="Utiliser les données de démonstration")
    p_report.add_argument("--force", action="store_true", help="Forcer le rafraîchissement MCP")
    sub.add_parser("tools", help="Lister les outils du serveur MCP Chariow")
    sub.add_parser("list", help="Lister les personas et leurs tâches")

    p_prompts = sub.add_parser("prompts", help="Afficher les prompts prêts à copier")
    p_prompts.add_argument("persona", help="Identifiant du persona")
    p_prompts.add_argument("--task", default=None, help="Tâche précise (sinon toutes)")
    p_prompts.add_argument("--demo", action="store_true", help="Contexte de démonstration")

    p_cron = sub.add_parser("cron", help="Générer la ligne crontab d'automatisation")
    p_cron.add_argument("--personas", default="marketing,ventes,finance",
                        help="Personas à planifier (séparés par des virgules)")
    p_cron.add_argument("--heure", default="7", help="Heure d'exécution (0-23)")

    p_obj = sub.add_parser("objectif", help="Tableau de bord : objectif de CA 30 jours (FCFA)")
    p_obj.add_argument("--demo", action="store_true", help="Utiliser les données de démonstration")
    p_obj.add_argument("--force", action="store_true", help="Forcer le rafraîchissement MCP")
    p_obj.add_argument("--cible", type=int, default=None,
                       help="Objectif en FCFA (défaut : KIMAGENT_OBJECTIF_XAF ou 800000)")
    p_obj.add_argument("--csv", type=Path, default=None,
                       help="Exporter la liste clients segmentée (prospection) à ce chemin")

    return parser


def _cmd_auth(args) -> int:
    from .oauth import authorize

    settings = Settings()
    try:
        authorize(force=True, mcp_url=settings.mcp_url)
        return 0
    except Exception as e:
        utils.err(str(e))
        return 1


def _cmd_fetch(args) -> int:
    from .oauth import auth_headers, authorize

    settings = Settings()
    ensure_dirs()
    if args.demo:
        from .pipeline import CACHE_FILE
        from .utils import write_json
        from .demo_data import get_demo_data

        write_json(CACHE_FILE, get_demo_data())
        utils.ok("Données de démonstration enregistrées dans data/store_data.json")
        return 0

    utils.step(f"Serveur MCP : {settings.mcp_url}")
    try:
        token = authorize() if not args.force else authorize(force=True, mcp_url=settings.mcp_url)
        headers = auth_headers(token) if token else None
    except Exception as e:
        utils.warn(f"Authentification incomplète : {e}")
        headers = None

    try:
        from .chariow_mcp import AuthRequiredError, fetch_store_data

        data = asyncio.run(fetch_store_data(settings, headers=headers))
    except (ChariowMCPError, AuthRequiredError) as e:
        utils.err(str(e))
        return 1

    from .pipeline import CACHE_FILE
    from .utils import write_json

    write_json(CACHE_FILE, data)
    utils.ok(f"Données enregistrées : data/store_data.json "
             f"({len(data.get('tools', {}))} outils)")
    if args.save:
        write_json(args.save, data)
        utils.ok(f"Copie de sauvegarde : {args.save}")
    return 0


def _cmd_run(args) -> int:
    settings = Settings()
    if args.persona is None:
        utils.info(utils._c("36", "Aucun persona fourni. "))  # noqa: SLF001
        print(list_personas_table())
        print("\nExemple : kimagent run marketing --demo")
        return 2

    try:
        persona = get_persona(args.persona)
    except KeyError as e:
        utils.err(str(e))
        print(list_personas_table())
        return 2

    task_ids = [t.strip() for t in args.tasks.split(",")] if args.tasks else None
    written = run_persona(
        persona,
        settings,
        demo=args.demo,
        force_fetch=args.force,
        task_ids=task_ids,
        no_brain=args.no_brain,
    )
    utils.ok(f"{len(written)} livrable(s) généré(s). Dossier : outputs/{persona.id}/")
    utils.info("Astuce : ouvrez les fichiers, puis lancez `kimagent run <persona>` avec "
               "KIMAGENT_BRAIN=anthropic dans .env pour la génération automatique.")
    return 0


def _cmd_report(args) -> int:
    from .pipeline import report

    print(report(demo=args.demo, force_fetch=getattr(args, "force", False)))
    return 0


def _cmd_tools(args) -> int:
    settings = Settings()
    utils.step(f"Interrogation du serveur MCP : {settings.mcp_url}")
    try:
        from .oauth import auth_headers, authorize

        token = authorize()
        headers = auth_headers(token) if token else None
    except Exception as e:
        utils.warn(f"Authentification non disponible ({e}) — tentative sans jeton.")
        headers = None
    try:
        tools = asyncio.run(list_mcp_tools(settings, headers=headers))
    except Exception as e:
        utils.err(f"Impossible de lister les outils : {e}")
        return 1
    if not tools:
        utils.warn("Aucun outil retourné (serveur peut exiger l'authentification OAuth).")
        return 1
    print(f"{len(tools)} outils disponibles sur le serveur MCP Chariow :\n")
    for t in tools:
        print(f"  • {t['name']}")
        if t.get("description"):
            print(f"      {t['description']}")
    return 0


def _cmd_list(args) -> int:
    print(list_personas_table())
    return 0


def _cmd_prompts(args) -> int:
    from .brain import compact_context
    from .demo_data import get_demo_data
    from .pipeline import load_data
    from .utils import truncate

    try:
        persona = get_persona(args.persona)
    except KeyError as e:
        utils.err(str(e))
        return 2

    data = load_data(Settings(), demo=args.demo)
    context = compact_context(data)
    tasks = [persona.task(args.task)] if args.task else persona.tasks
    for task in tasks:
        print("=" * 78)
        print(f"TÂCHE : {task.title}  ({task.output_file})")
        print("=" * 78)
        print(
            f"\nTu es : {persona.name}.\n{persona.system_prompt}\n\n"
            f"Réalise la tâche suivante :\n{task.prompt}\n\n"
            f"Utilise les données de ma boutique Chariow (via le connecteur MCP) pour tout "
            f"chiffre cité. Données de référence :\n\n{truncate(context, 8000)}\n"
        )
        print()
    return 0


def _cmd_objectif(args) -> int:
    from .pipeline import export_customers_csv, objectif_dashboard

    data = load_data(Settings(), force_fetch=args.force, demo=args.demo)
    print(objectif_dashboard(data, target_xaf=args.cible))
    if args.csv:
        try:
            path = export_customers_csv(data, args.csv)
            utils.ok(f"Liste clients segmentée exportée : {path}")
        except ValueError as e:
            utils.err(str(e))
            return 1
    return 0


def _cmd_cron(args) -> int:
    python = str(REPO_ROOT / ".venv" / "bin" / "python")
    kimagent = str(REPO_ROOT / "kimagent" / "cli.py")
    personas = [p.strip() for p in args.personas.split(",")]
    hour = int(args.heure)
    line = f"0 {hour} * * * cd {REPO_ROOT} && {python} {kimagent} run {','.join(personas)} --force >> {REPO_ROOT / 'logs' / 'kimagent.log'} 2>&1"
    print("Ajoutez cette ligne à votre crontab (`crontab -e`) :\n")
    print(f"  {line}")
    print("\nOu exécutez : scripts/install_cron.sh")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "auth":
        print(BANNER)

    handlers = {
        "auth": _cmd_auth,
        "fetch": _cmd_fetch,
        "run": _cmd_run,
        "report": _cmd_report,
        "tools": _cmd_tools,
        "list": _cmd_list,
        "prompts": _cmd_prompts,
        "cron": _cmd_cron,
        "objectif": _cmd_objectif,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
