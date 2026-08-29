"""Client du serveur MCP Chariow (https://mcp.chariow.com/public).

Récupère les données de votre boutique via les 21 outils officiels du serveur
MCP Chariow : produits, clients, ventes, remises, licences, webhooks et
analyses (store, ventes, clients, visites, conversion). Tous ces outils sont
en LECTURE SEULE : Kimagent ne peut pas modifier votre boutique via MCP.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

import httpx2
from mcp import ClientSession

from .config import Settings
from .utils import err, info, ok, step, warn

# Les 21 outils officiels du serveur MCP Chariow
MCP_TOOLS = [
    "global_search",
    "get_store",
    "list_products",
    "get_product",
    "list_customers",
    "get_customer",
    "list_sales",
    "get_sale",
    "list_discounts",
    "get_discount",
    "list_licenses",
    "get_license",
    "get_license_activations",
    "list_pulses",
    "get_pulse",
    "get_store_analytics",
    "get_sales_analytics",
    "get_customer_analytics",
    "get_visits_analytics",
    "get_conversion_rate_analytics",
]

# Appels par défaut pour chaque outil (aucun paramètre obligatoire pour la plupart)
DEFAULT_ARGS: dict[str, dict] = {
    "list_products": {"per_page": 100},
    "list_customers": {"per_page": 100},
    "list_sales": {"per_page": 100},
    "list_discounts": {"per_page": 100},
    "list_licenses": {"per_page": 100},
    "list_pulses": {"per_page": 100},
}


class AuthRequiredError(RuntimeError):
    pass


class ChariowMCPError(RuntimeError):
    pass


def _extract_text(result: Any) -> str:
    """Normalise un CallToolResult MCP en texte lisible."""
    if result is None:
        return ""
    # API mcp 2.x : result.content est une liste d'objets TextContent/ImageContent…
    content = getattr(result, "content", None)
    if content is None and isinstance(result, dict):
        content = result.get("content")
    if content is None:
        return str(result)

    parts: list[str] = []
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            else:
                parts.append(json.dumps(item, ensure_ascii=False, default=str))
        else:
            text = getattr(item, "text", None)
            parts.append(str(text if text is not None else item))
    return "\n".join(p for p in parts if p)


def _parse_result(text: str) -> Any:
    """Tente de parser le JSON renvoyé par l'outil, sinon renvoie le texte brut."""
    try:
        return json.loads(text)
    except Exception:
        return text


async def list_mcp_tools(settings: Settings, headers: dict | None = None) -> list[dict]:
    """Énumère les outils disponibles sur le serveur MCP (diagnostic)."""
    async with await _session(settings, headers) as session:
        tools = await session.list_tools()
        return [
            {"name": t.name, "description": (t.description or "")[:120]}
            for t in getattr(tools, "tools", [])
        ]


async def call_tool(settings: Settings, name: str, arguments: dict | None = None,
                    headers: dict | None = None) -> Any:
    """Appelle un outil MCP unique et renvoie sa valeur parsée."""
    async with await _session(settings, headers) as session:
        res = await session.call_tool(name, arguments or {})
        return _parse_result(_extract_text(res))


async def _session(settings: Settings, headers: dict | None):
    """Ouvre une session MCP (Streamable HTTP)."""

    from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

    hdrs = {"Accept": "application/json, text/event-stream"}
    if headers:
        hdrs.update(headers)

    timeout = httpx2.Timeout(30.0, read=180.0)
    http_client = create_mcp_http_client(headers=hdrs, timeout=timeout)

    streams = streamable_http_client(settings.mcp_url, http_client=http_client)

    class _Ctx:
        def __init__(self):
            self.http = http_client
            self.streams = streams
            self.session: Optional[ClientSession] = None

        async def __aenter__(self):
            self.ts = await self.streams.__aenter__()
            self.session = ClientSession(
                self.ts[0],
                self.ts[1],
                client_info={"name": "kimagent", "version": "1.0.0"},
            )
            await self.session.__aenter__()
            await self.session.initialize()
            return self.session

        async def __aexit__(self, *exc):
            # Nettoyage robuste : les erreurs de fermeture ne doivent jamais
            # masquer l'erreur d'origine (ni polluer la sortie).
            for closer in (
                lambda: self.session.__aexit__(*exc) if self.session else None,
                lambda: self.streams.__aexit__(*exc),
                lambda: self.http.__aexit__(*exc),
            ):
                try:
                    result = closer()
                    if result is not None:
                        await result
                except BaseException:
                    pass

    return _Ctx()


def _preflight(settings: Settings, headers: dict | None) -> None:
    """Vérifie que le serveur MCP est joignable AVANT d'ouvrir la session.

    Donne un message d'erreur clair et immédiat si le réseau bloque l'accès
    (cas fréquent : VPN/proxy/pare-feu), sans plonger dans les internals du SDK.
    """
    import httpx

    hdrs = {"Accept": "application/json, text/event-stream"}
    if headers:
        hdrs.update(headers)
    try:
        resp = httpx.get(settings.mcp_url, headers=hdrs, timeout=15, follow_redirects=True)
    except httpx.HTTPError as e:
        raise ChariowMCPError(
            f"Connexion au serveur MCP Chariow impossible ({settings.mcp_url}).\n"
            f"Détail : {e}\n"
            "Vérifiez votre connexion internet (un VPN/proxy peut bloquer l'accès), "
            "ou testez avec `kimagent fetch --demo`."
        ) from e
    if resp.status_code in (401, 403):
        raise AuthRequiredError(
            "Le serveur MCP Chariow demande une authentification.\n"
            "  → Lancez `kimagent auth` pour connecter votre compte Chariow."
        )


# ── Récupération complète des données de la boutique ─────────────────────────
async def fetch_store_data(
    settings: Settings,
    headers: dict | None = None,
    progress=None,
    tools: list[str] | None = None,
) -> dict:
    """Appelle tous les outils MCP Chariow et agrège les résultats.

    Retourne un dict : {"meta": {...}, "tools": {nom_outil: valeur_parsee}}
    """
    tools = tools or MCP_TOOLS
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}

    _preflight(settings, headers)

    try:
        async with await _session(settings, headers) as session:
            # Inventaire réel des outils exposés par le serveur
            try:
                available = await session.list_tools()
                available_names = {t.name for t in getattr(available, "tools", [])}
            except Exception:
                available_names = set(tools)
            info(f"Outils exposés par le serveur MCP : {len(available_names)}")

            for name in tools:
                if name not in available_names:
                    warn(f"Outil {name} non disponible sur ce serveur — ignoré.")
                    continue
                try:
                    if progress:
                        progress(name)
                    res = await session.call_tool(name, DEFAULT_ARGS.get(name, {}))
                    results[name] = _parse_result(_extract_text(res))
                except Exception as e:  # un outil en échec ne bloque pas le reste
                    errors[name] = str(e)
                    warn(f"Échec de l'outil {name} : {e}")
    except BaseExceptionGroup as eg:
        raise ChariowMCPError(
            f"Connexion au serveur MCP Chariow impossible ({settings.mcp_url}).\n"
            f"Détail : {_error_message(eg)}\n"
            "Vérifiez votre connexion internet (un VPN/proxy peut bloquer l'accès), "
            "ou testez avec `kimagent fetch --demo`."
        ) from eg
    except asyncio.CancelledError as ce:  # annulation interne du SDK sur échec de session
        raise ChariowMCPError(
            f"Session MCP Chariow interrompue ({settings.mcp_url}) : le serveur n'a pas "
            "répondu à l'initialisation. Vérifiez votre connexion internet, ou testez "
            "avec `kimagent fetch --demo`."
        ) from ce
    except Exception as e:
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg or "WWW-Authenticate" in msg:
            raise AuthRequiredError(
                "Le serveur MCP Chariow demande une authentification.\n"
                "  → Lancez `kimagent auth` pour vous connecter à votre compte Chariow."
            ) from e
        raise ChariowMCPError(
            f"Connexion au serveur MCP Chariow impossible ({settings.mcp_url}).\n"
            f"Détail : {msg}\n"
            "Vérifiez votre connexion internet, ou testez avec `kimagent fetch --demo`."
        ) from e

    data = {
        "meta": {
            "source": "chariow-mcp",
            "mcp_url": settings.mcp_url,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "tool_errors": errors,
        },
        "tools": results,
    }
    ok(f"{len(results)} outils MCP exécutés avec succès.")
    if errors:
        warn(f"{len(errors)} outil(s) en échec : {', '.join(errors)}")
    return data


# ── API REST Chariow (actions possibles, nécessite CHARIOW_API_KEY) ──────────
class ChariowAPI:
    """Client REST minimal https://api.chariow.com/v1 (actions = nécessitent la clé API).

    Le serveur MCP étant en lecture seule, les ACTIONS (ex. envoyer des
    invitations d'affiliation) passent par l'API REST avec CHARIOW_API_KEY.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base = settings.api_url.rstrip("/")

    def _headers(self) -> dict:
        key = self.settings.api_key
        if not key:
            raise RuntimeError(
                "Clé API manquante : renseignez CHARIOW_API_KEY dans le fichier .env "
                "(voir .env.example et docs/GUIDE_COMPLET.md)."
            )
        return {"Authorization": f"Bearer {key}", "Accept": "application/json"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{self.base}{path}", headers=self._headers(), params=params or {})
            if resp.status_code >= 400:
                raise RuntimeError(f"API Chariow {resp.status_code} sur {path} : {resp.text[:300]}")
            return resp.json().get("data", resp.json())

    def _post(self, path: str, payload: dict) -> dict:
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{self.base}{path}", headers=self._headers(), json=payload)
            if resp.status_code >= 400:
                raise RuntimeError(f"API Chariow {resp.status_code} sur {path} : {resp.text[:300]}")
            return resp.json().get("data", resp.json())

    def whoami(self) -> dict:
        return self._get("/store")

    def list_products(self, per_page: int = 100) -> dict:
        return self._get("/products", {"per_page": per_page})

    def list_sales(self, per_page: int = 100, status: str | None = None) -> dict:
        params: dict = {"per_page": per_page}
        if status:
            params["status"] = status
        return self._get("/sales", params)

    def send_affiliate_invitations(self, emails: list[str], message: str = "") -> dict:
        """Action concrète qui peut faire gagner de l'argent : invite des affiliés."""
        return self._post("/affiliates/invitations", {"emails": emails, "message": message})
