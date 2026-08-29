"""Interface graphique web de Kimagent (Flask).

Lancement :
    python -m kimagent gui [--host 127.0.0.1] [--port 5000] [--open]

Fonctions :
  * Tableau de bord — données boutique, cerveau IA configuré, état d'Ollama
  * Exécution des personas (agents IA) en un clic, avec journal en direct
  * Consultation et téléchargement des livrables générés (outputs/)
  * Rapport de synthèse et tableau de bord objectif de CA

Le serveur reste **local** : par défaut il n'écoute que sur 127.0.0.1,
aucune donnée ne quitte la machine (compatible Android/Termux —
ouvrez http://127.0.0.1:5000 dans le navigateur).
"""

from __future__ import annotations

import threading
import time
import webbrowser
from pathlib import Path

from . import utils
from .config import OUTPUTS_DIR, REPO_ROOT, Settings, ensure_dirs
from .demo_data import get_demo_data
from .personas import PERSONAS, get_persona, list_personas
from .pipeline import (
    CACHE_FILE,
    build_report,
    objectif_dashboard,
    run_persona,
)

try:
    from flask import (
        Flask,
        abort,
        jsonify,
        render_template,
        request,
        send_file,
    )
except ImportError:  # pragma: no cover
    raise ImportError(
        "L'interface graphique nécessite Flask : "
        ".venv/bin/pip install -r requirements.txt"
    ) from None

import markdown as md  # noqa: E402  (dépendance "markdown")


# ── Exécution en arrière-plan ─────────────────────────────────────────────────
RUNS: dict[str, dict] = {}
_RUNS_LOCK = threading.Lock()
_CURRENT_RUN = threading.local()
_RUN_COUNTER = 0

_ORIG_FUNCS: dict[str, object] = {}
_PATCHED: list[tuple[object, str, object]] = []  # (module, nom, valeur d'origine)
_CAPTURE_REFS = 0


def _append_log(kind: str, msg: str) -> None:
    rid = getattr(_CURRENT_RUN, "id", None)
    if not rid:
        return
    with _RUNS_LOCK:
        run = RUNS.get(rid)
        if run is None or run["status"] != "running":
            return
        run["logs"].append({"kind": kind, "msg": str(msg)})
        del run["logs"][:-500]


def _install_log_capture() -> None:
    """Redirige les messages du pipeline (utils.step/ok/…) vers le journal
    de l'exécution en cours (sans supprimer l'affichage console)."""
    global _CAPTURE_REFS
    names = ("step", "ok", "warn", "err", "info")
    for n in names:
        if n not in _ORIG_FUNCS:
            _ORIG_FUNCS[n] = getattr(utils, n)
    for n in names:
        orig = _ORIG_FUNCS[n]

        def make(orig=orig):
            def fn(msg, *a, **k):
                orig(msg, *a, **k)
                _append_log(n, msg)
            return fn

        setattr(utils, n, make())

    # brain.py importe err/warn directement : on patche ces références aussi
    try:
        from . import brain as _brain

        for n in ("err", "warn"):
            if not any(m is _brain and name == n for m, name, _ in _PATCHED):
                _PATCHED.append((_brain, n, getattr(_brain, n)))
                setattr(_brain, n, make(_ORIG_FUNCS[n]))
    except Exception:
        pass

    _CAPTURE_REFS += 1


def _restore_log_capture() -> None:
    """Restaure les fonctions d'origine (au dernier arrêt uniquement,
    si plusieurs exécutions tournent en parallèle)."""
    global _CAPTURE_REFS
    _CAPTURE_REFS -= 1
    if _CAPTURE_REFS > 0:
        return
    for n, orig in _ORIG_FUNCS.items():
        setattr(utils, n, orig)
    for mod, n, orig in _PATCHED:
        setattr(mod, n, orig)
    _PATCHED.clear()


def _start_run(
    persona_id: str,
    task_ids: list[str] | None,
    demo: bool,
    force: bool,
    no_brain: bool,
    ollama_model: str | None,
) -> str:
    global _RUN_COUNTER
    _RUN_COUNTER += 1
    run_id = f"run-{time.strftime('%H%M%S')}-{_RUN_COUNTER}"
    with _RUNS_LOCK:
        RUNS[run_id] = {
            "status": "running",
            "persona": persona_id,
            "logs": [],
            "written": [],
            "error": None,
            "started_at": time.strftime("%H:%M:%S"),
        }

    def worker() -> None:
        _CURRENT_RUN.id = run_id
        _install_log_capture()
        settings = Settings()
        try:
            if ollama_model and settings.brain_provider == "ollama":
                settings.ollama_model = ollama_model
            persona = get_persona(persona_id)
            written = run_persona(
                persona,
                settings,
                demo=demo,
                force_fetch=force,
                task_ids=task_ids,
                no_brain=no_brain,
            )
            entries = []
            for p in written:
                rel = p.relative_to(REPO_ROOT)
                parts = rel.parts  # outputs/<persona>/<date>/<fichier>
                entries.append({
                    "persona": parts[1],
                    "date": parts[2],
                    "name": parts[3],
                    "url": f"/outputs/view/{parts[1]}/{parts[2]}/{parts[3]}",
                })
            with _RUNS_LOCK:
                RUNS[run_id]["status"] = "done"
                RUNS[run_id]["written"] = entries
        except Exception as e:  # noqa: BLE001 — signalé à l'utilisateur
            with _RUNS_LOCK:
                RUNS[run_id]["status"] = "error"
                RUNS[run_id]["error"] = str(e)
        finally:
            _restore_log_capture()
            _CURRENT_RUN.id = None

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return run_id


def _run_state(run_id: str, since: int) -> dict:
    with _RUNS_LOCK:
        run = RUNS.get(run_id)
        if run is None:
            raise KeyError(run_id)
        return {
            "status": run["status"],
            "persona": run["persona"],
            "new_logs": run["logs"][since:],
            "total": len(run["logs"]),
            "written": run["written"],
            "error": run["error"],
        }


# ── Données du tableau de bord ────────────────────────────────────────────────
def _cached_data() -> dict | None:
    return utils.read_json(CACHE_FILE)


def _store_summary(data: dict | None) -> dict | None:
    if not data:
        return None
    tools = data.get("tools", data)
    store = tools.get("get_store") or {}
    summary = store.get("sales_summary") or {}
    an = tools.get("get_store_analytics") or {}
    sa = tools.get("get_sales_analytics") or {}
    meta = data.get("meta") or {}
    return {
        "name": store.get("name", "?"),
        "url": store.get("url", "?"),
        "currency": store.get("currency", "?"),
        "total_sales": summary.get("total_sales"),
        "total_revenue": utils.fmt_money(summary.get("total_revenue")),
        "customers": summary.get("total_customers"),
        "aov": utils.fmt_money(summary.get("avg_order_value")),
        "rev30": utils.fmt_money(summary.get("last_30_days_revenue") or sa.get("revenue")),
        "sales30": summary.get("last_30_days_sales", sa.get("sales_count")),
        "visits": an.get("visits"),
        "conversion": an.get("conversion_rate"),
        "source": meta.get("source", "?"),
        "fetched_at": meta.get("fetched_at", "?"),
        "age_h": utils.age_hours(CACHE_FILE) if CACHE_FILE.exists() else None,
    }


def _list_outputs() -> list[dict]:
    if not OUTPUTS_DIR.exists():
        return []
    result: list[dict] = []
    for pdir in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
        if not pdir.is_dir():
            continue
        for ddir in sorted(pdir.iterdir(), reverse=True):
            if not ddir.is_dir():
                continue
            files = []
            for f in sorted(ddir.iterdir()):
                if f.is_file() and not f.name.endswith(".tmp"):
                    st = f.stat()
                    files.append({
                        "name": f.name,
                        "size": st.st_size,
                        "mtime": time.strftime(
                            "%d/%m/%Y %H:%M", time.localtime(st.st_mtime)
                        ),
                    })
            if files:
                result.append({"persona": pdir.name, "date": ddir.name, "files": files})
    return result


_OLLAMA_CACHE: dict = {"at": 0.0, "value": None}


def _ollama_status(force: bool = False) -> dict:
    """État du serveur Ollama local (modèles disponibles). Cache 60 s."""
    now = time.time()
    if not force and _OLLAMA_CACHE["value"] is not None and now - _OLLAMA_CACHE["at"] < 60:
        return _OLLAMA_CACHE["value"]
    s = Settings()
    value = {"ok": False, "url": s.ollama_url, "models": [], "configured": s.ollama_model}
    try:
        import httpx

        r = httpx.get(f"{s.ollama_url.rstrip('/')}/api/tags", timeout=3)
        r.raise_for_status()
        value["ok"] = True
        value["models"] = [m.get("name", "?") for m in r.json().get("models", [])]
    except Exception as e:  # noqa: BLE001
        value["error"] = str(e)
    _OLLAMA_CACHE.update(at=now, value=value)
    return value


# ── Application Flask ─────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    ensure_dirs()

    @app.context_processor
    def _inject():
        return {"personas": list_personas()}

    def _render(page: str, **ctx) -> str:
        return render_template(page, **ctx)

    # ── Tableau de bord ──────────────────────────────────────────────────────
    @app.get("/")
    def index():
        data = _cached_data()
        store = _store_summary(data)
        settings = Settings()
        latest = _list_outputs()[:6]
        return _render(
            "dashboard.html",
            nav="home",
            title="Tableau de bord",
            store=store,
            store_age_h=store["age_h"] if store else None,
            settings=settings,
            ollama=_ollama_status(),
            latest=latest,
            outputs_count=len(_list_outputs()),
        )

    # ── Agents ──────────────────────────────────────────────────────────────
    @app.get("/agents")
    def agents():
        return _render("agents.html", nav="agents", title="Agents IA")

    # ── Exécution ────────────────────────────────────────────────────────────
    @app.get("/executer")
    def execute():
        settings = Settings()
        selected = request.args.get("persona", "marketing")
        if selected not in PERSONAS:
            selected = "marketing"
        return _render(
            "execute.html",
            nav="execute",
            title="Exécuter un agent",
            selected=selected,
            settings=settings,
            ollama=_ollama_status(),
        )

    @app.post("/api/run")
    def api_run():
        payload = request.get_json(silent=True) or {}
        persona_id = str(payload.get("persona", "")).strip()
        try:
            get_persona(persona_id)
        except KeyError as e:
            return jsonify(error=str(e)), 400
        tasks = [t for t in payload.get("tasks", []) if isinstance(t, str)] or None
        run_id = _start_run(
            persona_id=persona_id,
            task_ids=tasks,
            demo=bool(payload.get("demo")),
            force=bool(payload.get("force")),
            no_brain=bool(payload.get("no_brain")),
            ollama_model=str(payload.get("ollama_model") or "").strip() or None,
        )
        return jsonify(run_id=run_id)

    @app.get("/api/run/<run_id>")
    def api_run_state(run_id: str):
        try:
            since = max(0, int(request.args.get("since", 0)))
            state = _run_state(run_id, since)
        except KeyError:
            return jsonify(error="Exécution inconnue"), 404
        return jsonify(state)

    # ── Livrables ────────────────────────────────────────────────────────────
    @app.get("/outputs")
    def outputs():
        return _render(
            "outputs.html",
            nav="outputs",
            title="Livrables",
            groups=_list_outputs(),
        )

    def _safe_output_path(persona: str, date: str, fname: str) -> Path:
        path = (OUTPUTS_DIR / persona / date / fname).resolve()
        base = OUTPUTS_DIR.resolve()
        if not (path.is_file() and path.is_relative_to(base)):
            abort(404)
        return path

    @app.get("/outputs/view/<persona>/<date>/<path:fname>")
    def view_output(persona: str, date: str, fname: str):
        path = _safe_output_path(persona, date, fname)
        text = path.read_text(encoding="utf-8", errors="replace")
        html = md.markdown(
            text, extensions=["tables", "fenced_code", "sane_lists"]
        )
        return _render(
            "view.html",
            nav="outputs",
            title=fname,
            html=html,
            persona=persona,
            date=date,
            fname=fname,
        )

    @app.get("/outputs/download/<persona>/<date>/<path:fname>")
    def download_output(persona: str, date: str, fname: str):
        path = _safe_output_path(persona, date, fname)
        return send_file(path, as_attachment=True, download_name=fname)

    # ── Rapport & objectif ───────────────────────────────────────────────────
    @app.get("/rapport")
    def rapport():
        data = _cached_data()
        used_demo = data is None
        if used_demo:
            data = get_demo_data()
        text = build_report(data)
        html = md.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
        return _render(
            "page.html",
            nav="rapport",
            title="Rapport boutique",
            html=html,
            banner=(
                "Aucune donnée boutique en cache — affichage avec les données de "
                "démonstration. Lancez `kimagent fetch` (ou « Charger les données démo » "
                "sur le tableau de bord) pour voir votre vraie boutique."
                if used_demo
                else None
            ),
        )

    @app.get("/objectif")
    def objectif():
        data = _cached_data()
        used_demo = data is None
        if used_demo:
            data = get_demo_data()
        settings = Settings()
        text = objectif_dashboard(data, target_xaf=None)
        html = md.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
        return _render(
            "page.html",
            nav="objectif",
            title="Objectif de CA",
            html=html,
            banner=(
                "Aucune donnée boutique en cache — affichage avec les données de "
                "démonstration."
                if used_demo
                else None
            ),
        )

    # ── API diverses ─────────────────────────────────────────────────────────
    @app.get("/api/ollama")
    def api_ollama():
        return jsonify(_ollama_status())

    @app.post("/api/demo")
    def api_demo():
        utils.write_json(CACHE_FILE, get_demo_data())
        utils.ok("Données de démonstration enregistrées dans data/store_data.json")
        return jsonify(ok=True, url="/")

    @app.get("/healthz")
    def healthz():
        return jsonify(ok=True)

    @app.errorhandler(404)
    def _404(_e):
        return _render(
            "page.html",
            nav=None,
            title="Page introuvable",
            html="<p>Page introuvable. <a href=\"/'>Retour au tableau de bord</a>.</p>",
            banner=None,
        ), 404

    return app


def run_gui(host: str = "127.0.0.1", port: int = 5000, open_browser: bool = False) -> int:
    app = create_app()
    url = f"http://{'localhost' if host in ('0.0.0.0', '127.0.0.1') else host}:{port}"
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    utils.step(f"Interface web Kimagent : {url}")
    utils.info("Le serveur reste local. Arrêt avec Ctrl+C.")
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
    return 0
