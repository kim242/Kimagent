"""Connexion OAuth à Chariow (PKCE) avec stockage local et rafraîchissement du jeton.

Le serveur MCP Chariow utilise OAuth 2.0 : au premier lancement, `kimagent auth`
ouvre votre navigateur, vous vous connectez à votre compte Chariow, autorisez
l'accès, et le jeton est stocké localement dans `.chariow/token.json`
(jamais versionné). Les lancements suivants utilisent le jeton, avec
rafraîchissement automatique.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

import httpx

from .config import TOKEN_DIR
from .utils import err, info, ok, step, warn

CLIENT_ID = "kimagent"           # client public (sans secret) côté Chariow
REDIRECT_PORT = 38765
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/callback"
SCOPES = "store:read store:analytics:read"


class OAuthError(RuntimeError):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _pkce_pair() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(48))
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, _b64url(digest)


def token_path() -> Path:
    return TOKEN_DIR / "token.json"


def load_token() -> Optional[dict]:
    p = token_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_token(token: dict) -> None:
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    tmp = token_path().with_suffix(".tmp")
    tmp.write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(token_path())
    os.chmod(token_path(), 0o600)  # lisible uniquement par le propriétaire


# ── Découverte du serveur d'autorisation ──────────────────────────────────────
def _parse_www_authenticate(header: str) -> dict:
    """Analyse un en-tête WWW-Authenticate de type Bearer (RFC 6750)."""
    result: dict = {}
    for part in header.split(","):
        part = part.strip()
        if "=" in part:
            key, _, value = part.partition("=")
            result[key.strip()] = value.strip().strip('"')
        else:
            result[part] = True
    return result


def discover_auth_metadata(mcp_url: str) -> dict:
    """Découvre authorization_endpoint / token_endpoint du serveur MCP.

    Stratégie (dans l'ordre) :
      1. En-tête WWW-Authenticate de la réponse 401 (resource_metadata).
      2. /.well-known/oauth-protection-metadata (RFC 9728).
      3. /.well-known/oauth-authorization-server (RFC 8414).
    """
    parsed = urllib.parse.urlparse(mcp_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    with httpx.Client(timeout=20, follow_redirects=True) as client:
        try:
            resp = client.get(mcp_url, headers={"Accept": "application/json, text/event-stream"})
        except httpx.HTTPError as e:
            raise OAuthError(
                f"Impossible de joindre le serveur MCP {mcp_url} : {e}. "
                "Vérifiez votre connexion internet (un VPN ou un proxy peut bloquer l'accès)."
            )

        # 1) resource_metadata dans WWW-Authenticate
        if resp.status_code in (401, 403):
            www = resp.headers.get("www-authenticate", "")
            if "resource_metadata" in www:
                meta = _parse_www_authenticate(www)
                metadata_url = meta.get("resource_metadata")
                if metadata_url:
                    try:
                        m = client.get(metadata_url, timeout=20).json()
                        if m.get("authorization_endpoint"):
                            return m
                    except Exception:
                        pass

        # 2) oauth-protection-metadata
        for well_known in (
            f"{origin}/.well-known/oauth-protection-metadata",
            f"{origin}/.well-known/oauth-authorization-server",
        ):
            try:
                m = client.get(well_known, timeout=20).json()
                if m.get("authorization_endpoint") and m.get("token_endpoint"):
                    return m
            except Exception:
                continue

    raise OAuthError(
        "Le serveur MCP Chariow n'a pas exposé ses métadonnées OAuth de façon standard.\n"
        "  → Connectez d'abord votre boutique depuis l'un des outils pris en charge "
        "(Claude, ChatGPT, Cursor…) — voir mcp/setup.md — puis réessayez `kimagent auth`.\n"
        "  → Ou utilisez le mode API : renseignez CHARIOW_API_KEY dans .env."
    )


# ── Mini-serveur local pour recevoir le code d'autorisation ──────────────────
class _CallbackHandler(BaseHTTPRequestHandler):
    code: Optional[str] = None

    def do_GET(self):  # noqa: N802
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" in params:
            _CallbackHandler.code = params["code"][0]
            body = "<h1>Connexion réussie !</h1><p>Vous pouvez fermer cet onglet et revenir au terminal.</p>".encode("utf-8")
            self.send_response(200)
        else:
            _CallbackHandler.code = None
            body = "<h1>Connexion annulée ou échouée.</h1><p>Fermez cet onglet.</p>".encode("utf-8")
            self.send_response(400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence
        pass


def _wait_for_code(timeout: float = 180.0) -> Optional[str]:
    server = HTTPServer(("127.0.0.1", REDIRECT_PORT), _CallbackHandler)
    deadline = time.time() + timeout
    while time.time() < deadline:
        server.handle_request()
        if _CallbackHandler.code is not None:
            server.server_close()
            return _CallbackHandler.code
    server.server_close()
    return None


# ── Flux complet ──────────────────────────────────────────────────────────────
def _exchange_code(token_endpoint: str, code: str, verifier: str) -> dict:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(token_endpoint, data=payload)
        if resp.status_code >= 400:
            raise OAuthError(f"Échange du code OAuth refusé ({resp.status_code}) : {resp.text[:300]}")
        data = resp.json()
    data["expires_at"] = time.time() + int(data.get("expires_in", 3600))
    return data


def _refresh_token(token_endpoint: str, token: dict) -> dict:
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
        "client_id": CLIENT_ID,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(token_endpoint, data=payload)
        if resp.status_code >= 400:
            raise OAuthError(f"Rafraîchissement du jeton refusé ({resp.status_code}) : {resp.text[:300]}")
        data = resp.json()
    data["expires_at"] = time.time() + int(data.get("expires_in", 3600))
    return data


def authorize(force: bool = False, mcp_url: str = "https://mcp.chariow.com/public") -> dict:
    """Retourne un jeton valide (charge, rafraîchit ou lance la connexion)."""
    token = None if force else load_token()

    if token and token.get("access_token"):
        # Jeton encore valide ?
        if token.get("expires_at", 0) > time.time() + 60:
            return token
        # Expiré mais rafraîchissable ?
        if token.get("refresh_token"):
            try:
                meta = discover_auth_metadata(mcp_url)
                step("Jeton expiré — rafraîchissement…")
                token = _refresh_token(meta["token_endpoint"], token)
                save_token(token)
                ok("Jeton rafraîchi.")
                return token
            except OAuthError as e:
                warn(f"Rafraîchissement impossible ({e}). Reconnexion complète…")
        token = None

    # Connexion interactive
    meta = discover_auth_metadata(mcp_url)
    verifier, challenge = _pkce_pair()
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": secrets.token_urlsafe(16),
    }
    auth_url = meta["authorization_endpoint"] + "?" + urllib.parse.urlencode(params)

    info("Ouverture du navigateur pour autoriser Kimagent sur votre compte Chariow…")
    webbrowser.open(auth_url)
    print(f"  Si rien ne s'ouvre, copiez cette adresse dans votre navigateur :\n  {auth_url}")

    # Petit serveur local pour recevoir le callback (dans un thread pour éviter les blocages)
    _CallbackHandler.code = None
    code = _wait_for_code()
    if not code:
        raise OAuthError("Connexion annulée (délai dépassé). Relancez `kimagent auth`.")

    token = _exchange_code(meta["token_endpoint"], code, verifier)
    save_token(token)
    ok("Connexion Chariow réussie ! Jeton enregistré.")
    return token


def auth_headers(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}
