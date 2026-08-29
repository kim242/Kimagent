# 🤖 Kimagent — Votre boutique Chariow pilotée par l'IA

**Kimagent** connecte des agents IA à votre boutique [Chariow](https://chariow.com)
via le serveur MCP officiel (`https://mcp.chariow.com/public`) et génère
automatiquement du contenu et des stratégies **pour faire gagner de l'argent** :
contenus marketing, optimisation des ventes, audit produits, analyses
financières, relances clients et programme d'affiliation.

## ✨ Ce que Kimagent fait pour vous

| Agent (persona) | Ce qu'il génère | Exemple de livrable |
|---|---|---|
| **marketing** | Calendrier éditorial 30 jours, posts réseaux sociaux, séquences email, pages produit optimisées | 10 posts prêts à publier |
| **ventes** | Diagnostic de la boutique, plan d'upsell/cross-sell, stratégie de prix & promotions | 5 leviers de conversion chiffrés |
| **produit** | Audit de l'offre, idées de nouveaux produits, bundles rentables | 5 nouveaux produits estimés |
| **finance** | Bilan 30 jours, analyse des clients à forte valeur | Revenus par produit, recommandations |
| **support** | Campagnes paniers abandonnés, réactivation clients, collecte d'avis | 3 emails de relance prêts à envoyer |
| **affiliation** | Audit du programme, plan de recrutement, kit de vente pour affiliés | Email d'invitation affiliés |
| **ebook** | Analyse marché, plan, **rédaction complète d'e-books**, page de vente, couverture | E-book 4 000-8 000 mots prêt à publier |
| **objectif** | Analyse d'écart, plan de vente 30 jours, prospection clients, offres, suivi | **800 000 FCFA de CA en 30 jours**, avec tableau de bord quotidien |

## 🚀 Démarrage rapide (2 minutes)

```bash
# 1. Installer
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # puis ouvrez .env et choisissez votre cerveau IA

# 2. (Facultatif) Connecter votre boutique Chariow — une seule fois
.venv/bin/python -m kimagent auth

# 3. Essayer immédiatement avec une boutique de démonstration
.venv/bin/python -m kimagent run marketing --demo --no-brain

# 4. Passer à votre vraie boutique
.venv/bin/python -m kimagent fetch
.venv/bin/python -m kimagent run marketing
.venv/bin/python -m kimagent report
```

## 📱 Démarrage rapide sur Android (Termux + Ollama)

Kimagent fonctionne **100 % localement sur Android** grâce à Termux et Ollama —
aucun serveur distant, aucune clé API payante.

```bash
# Dans Termux (installez-le depuis F-Droid, pas Play Store)
pkg install python git curl
git clone https://github.com/kim242/Kimagent.git && cd Kimagent

# Installation automatique tout-en-un
bash scripts/install_termux.sh
```

> 📖 Guide détaillé : [`docs/TERMUX_OLLAMA.md`](docs/TERMUX_OLLAMA.md)

Les livrables sont écrits dans `outputs/<persona>/<date>/`.

## ⚙️ Choisir le cerveau IA

Dans `.env` :

| `KIMAGENT_BRAIN` | Clé requise | Usage |
|---|---|---|
| `none` | — | Kimagent écrit des **prompts prêts à copier** dans Claude Desktop, ChatGPT, Cursor… (recommandé pour démarrer, gratuit) |
| `anthropic` | `ANTHROPIC_API_KEY` | Génération automatique avec Claude |
| `openai` | `OPENAI_API_KEY` | Génération automatique avec GPT |
| `ollama` | — | Modèle local gratuit (Ollama) — fonctionne aussi sur Android (Termux) |

## 📦 Contenu du dépôt

```
kimagent/          Agent Python (CLI) : auth, fetch, run, report…
agents/personas/   Les 6 agents IA + leurs prompts prêts à l'emploi (Markdown)
mcp/               Configs & guides de connexion (Claude, ChatGPT, Cursor, Windsurf)
docs/              Guide complet en français
scripts/           Scripts d'automatisation (cron)
tests/             Tests
```

## 🔐 Sécurité

- Le serveur MCP Chariow est **en lecture seule** : Kimagent ne peut pas modifier
  votre boutique (21 outils officiels de lecture).
- Vos jetons OAuth sont stockés localement dans `.chariow/` (jamais versionnés).
- Les actions (ex. invitations affiliés) ne sont possibles qu'avec votre clé API
  `CHARIOW_API_KEY`, que vous contrôlez.
- Ne committez jamais `.env` ni `.chariow/` (déjà dans `.gitignore`).

## 📚 Documentation

- **Guide complet** : [`docs/GUIDE_COMPLET.md`](docs/GUIDE_COMPLET.md)
- **Android / Termux + Ollama** : [`docs/TERMUX_OLLAMA.md`](docs/TERMUX_OLLAMA.md)
- **Connexion des outils IA** : [`mcp/setup.md`](mcp/setup.md)
- **Les 21 outils MCP** : [`mcp/tools.md`](mcp/tools.md)
- **Sécurité** : [`mcp/security.md`](mcp/security.md)

> Kimagent est un projet indépendant. Il utilise le serveur MCP public de
> Chariow (`https://mcp.chariow.com/public`) et l'API publique
> (`https://api.chariow.com/v1`), conformément à la documentation développeur
> de Chariow ([chariow.dev](https://chariow.dev)).
