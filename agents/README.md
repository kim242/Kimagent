# 🤖 Les 6 agents IA de Kimagent

Ce dossier contient les **personas** de Kimagent : des agents spécialisés,
chacun avec un rôle, un prompt système et des missions concrètes pour **faire
gagner de l'argent** avec votre boutique Chariow.

## Les 6 agents

| Fichier | Agent | Il fait gagner de l'argent en… |
|---|---|---|
| [`marketing.md`](marketing.md) | Contenus & Marketing | créant des contenus qui vendent (posts, emails, pages produit) |
| [`ventes.md`](ventes.md) | Optimisation des Ventes | trouvant les leviers de conversion et les promotions rentables |
| [`produit.md`](produit.md) | Audit Produits | améliorant l'offre, créant bundles et nouveaux produits |
| [`finance.md`](finance.md) | Analyse Financière | identifiant où l'argent se gagne et se perd |
| [`support.md`](support.md) | Relation Client & Relances | récupérant les paniers abandonnés et fidélisant |
| [`affiliation.md`](affiliation.md) | Programme d'Affiliation | déployant un réseau d'affiliés qui vendent pour vous |

## Deux façons de les utiliser

**1. Manuellement (gratuit, sans clé API)**
Connectez votre IA (Claude, ChatGPT, Cursor) à Chariow — voir
[`mcp/setup.md`](../../mcp/setup.md) — puis copiez le prompt système et les
missions du persona dans une conversation.

**2. Automatiquement avec Kimagent**
```bash
.venv/bin/python -m kimagent run marketing    # tous les livrables du persona
.venv/bin/python -m kimagent run ventes --tasks diagnostic,pricing
```
Avec `KIMAGENT_BRAIN=anthropic|openai|ollama` dans `.env`, Kimagent génère
les livrables tout seul dans `outputs/<persona>/<date>/`. Sans cerveau
(`none`), il écrit des prompts prêts à copier.

## Personnaliser

Les personas sont définis dans `kimagent/personas.py` : ajoutez une tâche à un
agent existant ou créez votre propre agent (par exemple « SEO », « TikTok »,
« Newsletter ») — c'est là que Kimagent apprend de nouvelles façons de créer
de la valeur.
