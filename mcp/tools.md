# 🛠 Les 21 outils du serveur MCP Chariow

Le serveur `https://mcp.chariow.com/public` expose **21 outils en lecture
seule** (aucun ne modifie votre boutique). Kimagent les appelle tous pour
construire une vue complète de votre activité.

| # | Outil | Rôle |
|---|---|---|
| 1 | `global_search` | Recherche dans toute la boutique (produits, clients, ventes, remises) |
| 2 | `get_store` | Profil, réglages et résumé des ventes de la boutique |
| 3 | `list_products` | Liste des produits (filtres : statut, catégorie, type) |
| 4 | `get_product` | Détail complet d'un produit (FAQ, paliers, livrables, SEO…) |
| 5 | `list_customers` | Liste des clients (recherche par nom/email) |
| 6 | `get_customer` | Profil complet d'un client |
| 7 | `list_sales` | Ventes (filtres : statut, période, client) |
| 8 | `get_sale` | Détail d'une vente |
| 9 | `list_discounts` | Codes de remise (filtres : statut, recherche) |
| 10 | `get_discount` | Détail d'un code de remise (usages, limites) |
| 11 | `list_licenses` | Licences émises (filtres : statut, client, produit) |
| 12 | `get_license` | Détail d'une licence (activations, expiration) |
| 13 | `get_license_activations` | Historique d'activations d'une licence |
| 14 | `list_pulses` | Configurations de webhooks (Pulse) |
| 15 | `get_pulse` | Détail d'un webhook |
| 16 | `get_store_analytics` | Performance globale (visites, conversions, ventes) |
| 17 | `get_sales_analytics` | Analyse détaillée des revenus et ventes |
| 18 | `get_customer_analytics` | Insights clients (nouveaux/retours, géographie) |
| 19 | `get_visits_analytics` | Analyse du trafic (sources, appareils, pays) |
| 20 | `get_conversion_rate_analytics` | Taux de conversion (appareil, pays, produit) |
| 21 | *(v1.1+)* Extensions : cours, coaching, règlements, affiliation, infrastructure | Détection automatique par `kimagent tools` |

## Exemples de demandes en langage naturel

- « *Quelles sont mes ventes d'aujourd'hui ?* » → `list_sales`
- « *Trouve le client marie@example.com* » → `list_customers` / `get_customer`
- « *Quel est mon taux de conversion ce mois-ci ?* » → `get_conversion_rate_analytics`
- « *Combien d'activations reste-t-il sur la licence ABC-123 ?* » → `get_license`
- « *Cherche « premium » dans ma boutique* » → `global_search`

## Voir les outils depuis Kimagent

```bash
.venv/bin/python -m kimagent tools
```

Affiche la liste exacte des outils exposés par le serveur au moment de la
connexion (le serveur peut évoluer, la version 1.1.0 en compte 44 capacités
consolidées en interfaces multi-modes).
