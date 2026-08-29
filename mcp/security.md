# 🔐 Sécurité des données avec Chariow MCP

## Ce que le serveur MCP peut voir

Le serveur MCP Chariow donne à l'IA connectée un accès **en lecture** aux
données de votre boutique : produits, ventes, clients (noms, emails, pays),
licences, remises, webhooks et statistiques. C'est exactement ce qu'il faut
pour analyser et créer du contenu — mais ce sont des données sensibles.

## Règles d'or

1. **Le MCP est en lecture seule.** Aucun outil MCP ne peut modifier votre
   boutique. Si un assistant propose de « modifier » un produit via MCP,
   c'est impossible — les actions passent par l'API REST (`api.chariow.com/v1`)
   avec votre clé API `CHARIOW_API_KEY`, que vous contrôlez.
2. **Ne partagez jamais vos jetons.** Le jeton OAuth Kimagent vit dans
   `.chariow/token.json` (mode 600, ignoré par Git). Ne le collez pas dans un
   chat, un fichier versionné ou un prompt.
3. **Ne committez jamais `.env` ni `data/`.** Les données extraites de la
   boutique (`data/store_data.json`) contiennent des clients — elles restent
   locales (`.gitignore` les exclut).
4. **Révoquez l'accès si besoin.** `app.chariow.com` → **Paramètres → API
   Keys** → révoquez la connexion MCP ou la clé API.
5. **Vérifiez les livrables avant publication.** Les contenus générés par IA
   (posts, emails) doivent être relus : ils peuvent contenir des chiffres
   approximatifs — faites vérifier par Kimagent (`kimagent report`) avant de
   publier des montants.

## Limites de débit

- Serveur MCP : **60 requêtes/minute**.
- API REST : **100 requêtes/minute** par clé.

Kimagent gère le cache local (`data/store_data.json`, 12 h par défaut) pour
éviter de marteler l'API à chaque génération.

## Quand faut-il une clé API ?

| Besoin | MCP (OAuth) | API REST (clé) |
|---|---|---|
| Lire produits, ventes, clients, analytics | ✅ | ✅ |
| Générer contenus/stratégies (Kimagent) | ✅ | — |
| Créer un checkout / vendre | — | ✅ |
| Envoyer des invitations affiliés | — | ✅ |
| Activer/révoquer des licences | — | ✅ |

> En résumé : pour **gagner de l'argent** avec Kimagent, le MCP suffit
> (analyse + création). La clé API n'est nécessaire que pour les actions.
