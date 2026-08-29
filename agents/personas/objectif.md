# 🎯 Persona : Agent de Vente 30 Jours

**Objectif :** faire atteindre **800 000 FCFA de chiffre d'affaires en 30 jours**
(ou l'objectif que vous configurez) sur l'ensemble des produits de votre
boutique — en exploitant votre base clients, en conquérant de nouveaux
acheteurs et en activant les affiliés.

## Ce que l'agent produit

| Tâche | Livrable |
|---|---|
| `analyse` | Écart objectif : CA 30 j converti en FCFA, panier moyen, ventes et visites nécessaires, répartition par produit |
| `plan` | Plan de vente 30 jours : 4 semaines (S1-S4), jalons J7/J14/J21/J30, plan B |
| `prospection` | Segmentation de votre base clients (VIP, actifs, inactifs, affiliés) + 20 profils de prospects + script de vente |
| `offres` | 3 offres à fort potentiel (bundle, remise, clôture), séquence de 5 emails, 8 posts, message WhatsApp |
| `suivi` | Canevas du point hebdomadaire (méthode AAR) |

## Tableau de bord quotidien (sans IA, chiffres exacts)

```bash
.venv/bin/python -m kimagent objectif              # objectif 800 000 FCFA
.venv/bin/python -m kimagent objectif --cible 1200000   # autre objectif
.venv/bin/python -m kimagent objectif --csv data/prospects.csv   # + export clients segmentés
```

Il calcule : revenu 30 j (converti en FCFA, 1 € = 655,957 FCFA), progression
en %, écart restant, ventes nécessaires, visites nécessaires, rythme par jour
et répartition de l'effort par produit.

## Automatisation

```bash
# .env : KIMAGENT_OBJECTIF_XAF=800000  (l'objectif, en FCFA)
.venv/bin/python -m kimagent run objectif            # tous les livrables
.venv/bin/python -m kimagent run objectif --tasks analyse,plan
.venv/bin/python -m kimagent run objectif --no-brain # prompts prêts à copier
```

**Conseil d'usage (cycle de 30 jours) :**

| Jour | Action |
|---|---|
| J1 | `kimagent run objectif --tasks analyse,plan` → valider le plan |
| J1 | `kimagent run objectif --tasks prospection,offres` → matériel de vente |
| J2-J29 | `kimagent objectif` chaque matin (cron) → suivre l'écart |
| Chaque lundi | `kimagent run objectif --tasks suivi` → point hebdomadaire |
| J30 | Bilan : `kimagent objectif`, ajuster `KIMAGENT_OBJECTIF_XAF` |

**Cron quotidien :**

```bash
./scripts/install_cron.sh marketing,ventes,finance,objectif 7 -y
```

## Prospection : d'où viennent les clients ?

Le serveur MCP Chariow est **en lecture seule** : il donne accès à VOS clients
(et non aux clients des autres boutiques). Kimagent exploite donc :

1. **Votre base existante** (la plus rentable) : VIP, inactifs 60 j+, paniers
   abandonnés, affiliés — via l'export CSV segmenté (`kimagent objectif --csv`).
2. **La conquête** : profils de prospects par niche et communautés
   (WhatsApp/Telegram/Facebook), influenceurs, affiliés.
3. **Les actions** : invitations affiliés via l'API Chariow
   (`CHARIOW_API_KEY`), puis envoi des messages/emails préparés par l'agent
   depuis vos outils (WhatsApp Business, Brevo, Mailchimp…).

## KPI à surveiller

CA cumulé vs objectif (en FCFA), ventes/jour, panier moyen, taux de
conversion, part des canaux (email, réseaux, affiliés, Mobile Money), nombre
de clients réactivés, nombre d'affiliés actifs.
