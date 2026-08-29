# CLAUDE.md — Instructions pour les agents IA travaillant dans ce dépôt

Ce dépôt contient **Kimagent**, un agent IA qui pilote la boutique Chariow de
l'utilisateur via le serveur MCP officiel `https://mcp.chariow.com/public`.

## Pourquoi ce dépôt existe

L'utilisateur veut que des agents IA **créent du contenu et lui fassent gagner
de l'argent** à partir des données de sa boutique Chariow (ventes, produits,
clients, analytics). Kimagent automatise ce travail.

## Contexte Chariow (à connaître)

- **Serveur MCP** : `https://mcp.chariow.com/public` — 21 outils **en lecture
  seule** (produits, clients, ventes, remises, licences, webhooks, analytics).
  Authentification OAuth (le jeton est stocké dans `.chariow/token.json`).
- **API REST** : `https://api.chariow.com/v1` — nécessite `CHARIOW_API_KEY`
  (actions uniquement ; MCP = lecture seule).
- **Limites** : 60 requêtes/min sur MCP, 100 req/min sur l'API REST.

## Commandes Kimagent

```bash
.venv/bin/python -m kimagent auth        # OAuth Chariow (une seule fois)
.venv/bin/python -m kimagent fetch       # données boutique → data/store_data.json
.venv/bin/python -m kimagent report      # rapport de synthèse
.venv/bin/python -m kimagent list        # personas et tâches disponibles
.venv/bin/python -m kimagent run <persona> [--tasks a,b] [--demo] [--no-brain]
.venv/bin/python -m kimagent prompts <persona> [--task X]
.venv/bin/python -m kimagent gui [--host 127.0.0.1] [--port 5000] [--open]
```

## Ce que les agents IA (vous) pouvez faire dans ce dépôt

1. **Générer des livrables** : `kimagent run <persona>` produit des fichiers
   dans `outputs/<persona>/<date>/`. En mode `none` (défaut), il écrit des
   prompts prêts à copier ; avec `KIMAGENT_BRAIN=anthropic|openai|ollama`
   dans `.env`, il génère le contenu directement.
2. **Améliorer Kimagent** : le code est dans `kimagent/` (CLI, MCP client,
   OAuth, brain LLM agnostique, personas). Les personas/tâches sont définis
   dans `kimagent/personas.py` — c'est là qu'on ajoute de nouvelles façons de
   faire gagner de l'argent.
3. **Ne jamais** : committer `.env`, `.chariow/`, `data/`, `outputs/` (ignorés).

## Règles d'or

- Les données de la boutique sont **confidentielles** (clients, revenus) —
  ne les citez jamais hors des livrables, ne les committez pas.
- Le MCP Chariow est en lecture seule : ne laissez pas entendre que l'agent
  modifie la boutique via MCP. Les actions passent par l'API REST avec la clé.
- Répondez à l'utilisateur en **français**.
