# 📘 Guide complet — Kimagent × Chariow

> Connecter des agents IA à votre boutique Chariow via MCP pour **créer du
> contenu et gagner de l'argent**.

---

## 1. De quoi s'agit-il ?

**Chariow** est une plateforme e-commerce pour produits numériques (cours,
templates, logiciels, ebooks, coaching, licences). Elle expose deux interfaces
pour les développeurs et les IA :

| Interface | Adresse | Accès |
|---|---|---|
| **Serveur MCP** | `https://mcp.chariow.com/public` | 21+ outils **lecture seule** — produits, ventes, clients, analytics |
| **API REST** | `https://api.chariow.com/v1` | Lecture **et** actions (checkout, licences, invitations affiliés) — nécessite une clé API |

**Kimagent** est l'agent qui exploite ces interfaces : il récupère les données
de votre boutique, les analyse, et génère automatiquement des livrables
concrets (posts, emails, pages produit, stratégies de prix, campagnes de
relance, plans d'affiliation, **e-books professionnels complets**…).

---

## 2. Installation

```bash
git clone <votre-dépôt> Kimagent && cd Kimagent
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Ou en une commande : `./scripts/quickstart.sh`

### 2.1 Choisir le cerveau IA (`.env`)

| `KIMAGENT_BRAIN` | Clé requise | Description |
|---|---|---|
| `none` *(défaut)* | — | Écrit des **prompts prêts à copier** dans Claude/ChatGPT/Cursor. Gratuit. |
| `anthropic` | `ANTHROPIC_API_KEY` | Génération automatique avec Claude |
| `openai` | `OPENAI_API_KEY` | Génération automatique avec GPT |
| `ollama` | — | Modèle local gratuit (installer [Ollama](https://ollama.com)) |

---

## 3. Connecter votre boutique

### 3.1 Via Kimagent (recommandé)

```bash
.venv/bin/python -m kimagent auth
```

Un navigateur s'ouvre → connexion à votre compte Chariow → autorisation.
Le jeton OAuth est stocké dans `.chariow/token.json` (mode 600) et se
rafraîchit automatiquement. Aucune clé API nécessaire pour la lecture.

### 3.2 Via vos outils IA habituels

Claude Desktop, Claude.ai, ChatGPT, Cursor, Windsurf ou Claude Code :
voir [`mcp/setup.md`](../mcp/setup.md). Dans tous les cas, l'URL est
`https://mcp.chariow.com/public`.

---

## 4. Récupérer les données de la boutique

```bash
.venv/bin/python -m kimagent fetch          # appel MCP complet (21 outils)
.venv/bin/python -m kimagent fetch --force  # ignore le cache local
.venv/bin/python -m kimagent report         # rapport de synthèse
```

Les données sont mises en cache dans `data/store_data.json` (12 h par défaut,
réglable via `KIMAGENT_DATA_MAX_AGE_H`). Le cache évite de dépasser la limite
de 60 requêtes/min du serveur MCP.

> 💡 **Test sans boutique** : toutes les commandes acceptent `--demo` avec une
> boutique fictive réaliste (`kimagent report --demo`, `kimagent run marketing --demo`).

---

## 5. Générer des livrables avec les agents

### 5.1 Les 8 personas

| Persona | Tâches (livrables) |
|---|---|
| `marketing` | calendrier 30 j, 10 posts, séquence email, pages produit |
| `ventes` | diagnostic, upsell/cross-sell, prix & promotions |
| `produit` | audit offre, nouveaux produits, bundles |
| `finance` | bilan 30 j, clients à forte valeur |
| `support` | paniers abandonnés, réactivation, avis |
| `affiliation` | audit programme, recrutement, kit de vente |
| `ebook` | analyse marché, plan, **rédaction complète d'e-book**, page de vente, couverture |
| `objectif` | **objectif CA 30 jours (800 000 FCFA)** : analyse d'écart, plan de vente, prospection, offres, suivi |

### 5.2 Lancer un agent

```bash
.venv/bin/python -m kimagent run marketing                 # toutes les tâches
.venv/bin/python -m kimagent run ventes --tasks diagnostic # une tâche précise
.venv/bin/python -m kimagent run produit --demo            # boutique fictive
.venv/bin/python -m kimagent run marketing --no-brain      # prompts à copier
```

Résultat : `outputs/<persona>/<date>/…md`

### 5.3 Mode automatique (avec cerveau)

```bash
# .env : KIMAGENT_BRAIN=anthropic (ou openai, ollama)
.venv/bin/python -m kimagent run marketing
```

Kimagent appelle Claude/GPT/Ollama avec (1) le rôle du persona, (2) la tâche,
(3) les données réelles de la boutique, puis écrit le livrable final.

### 5.4 Mode manuel (sans cerveau)

```bash
.venv/bin/python -m kimagent run marketing --no-brain
.venv/bin/python -m kimagent prompts ventes --task diagnostic
```

Kimagent écrit des **prompts prêts à copier** : ouvrez Claude Desktop ou
ChatGPT (connecté à Chariow), collez le prompt, et collez la réponse dans le
fichier. Les prompts sont aussi disponibles dans [`agents/personas/`](../agents/personas/).

### 5.5 Interface graphique (web)

Au lieu de la ligne de commande, Kimagent fournit une interface web **100 %
locale** (Flask). Utile sur bureau, et sur **Android/Termux** où Tkinter est
indisponible :

```bash
.venv/bin/python -m kimagent gui            # → http://127.0.0.1:5000
.venv/bin/python -m kimagent gui --open     # et ouvre le navigateur
```

Sur Android, ouvrez `http://127.0.0.1:5000` dans Chrome. Le serveur n'écoute
que sur `127.0.0.1` par défaut : aucune donnée ne quitte la machine.

- **Tableau de bord** : chiffres boutique, cerveau IA, état d'Ollama (modèles).
- **Exécuter** : lancez un agent en un clic, avec journal en direct.
- **Livrables** : consultation et téléchargement des fichiers générés.
- **Rapport / Objectif** : synthèse boutique et tableau de bord CA (FCFA).

---

## 6. Automatiser (cron)

Génère les livrables chaque matin automatiquement :

```bash
.venv/bin/python -m kimagent cron --personas marketing,ventes,finance --heure 7
# ou
./scripts/install_cron.sh marketing,ventes,finance 7 -y
```

Les logs vont dans `logs/kimagent.log`.

---

## 7. Actions (nécessite la clé API)

Le MCP est en lecture seule. Pour **agir** sur la boutique (envoyer des
invitations affiliés, créer des checkouts, gérer des licences), utilisez
l'API REST avec `CHARIOW_API_KEY` dans `.env` :

```python
from kimagent.config import Settings
from kimagent.chariow_mcp import ChariowAPI

api = ChariowAPI(Settings())
print(api.whoami())
api.send_affiliate_invitations(["a@ex.com", "b@ex.com"], "20 % de commission !")
```

Créez la clé dans `app.chariow.com` → **Paramètres → API Keys**.
Limite : 100 requêtes/min. Ne committez jamais `.env`.

---

## 8. Exemples concrets « gagner de l'argent »

1. **Lundi matin** — `kimagent run marketing` → 10 posts + calendrier de la
   semaine publiés sur vos réseaux.
2. **Chaque matin** — cron → rapport ventes de la veille dans `outputs/finance/`.
3. **Panier moyen bas ?** — `kimagent run ventes --tasks upsells` → plan
   d'upsell immédiat (ex. proposer le bundle après l'achat de l'ebook).
4. **Clients inactifs ?** — `kimagent run support --tasks reactivation` →
   séquence d'emails prête à envoyer via votre outil d'emailing.
5. **Lancer l'affiliation** — `kimagent run affiliation` + invitations via
   l'API → des tiers vendent pour vous 24h/24.
6. **Créer un e-book qui se vend** — `kimagent run ebook` : l'agent analyse
   les meilleures ventes de votre boutique, choisit le sujet le plus rentable,
   rédige l'e-book complet, puis fournit la fiche produit Chariow et la page
   de vente prêtes à publier (voir [`agents/personas/ebook.md`](../agents/personas/ebook.md)).
7. **Atteindre 800 000 FCFA / 30 jours** — `kimagent run objectif` pour le
   plan de vente, la prospection et les offres ; puis `kimagent objectif`
   chaque matin pour suivre l'écart (ventes/visites nécessaires, rythme par
   jour) ; `kimagent objectif --csv` exporte la liste clients segmentée
   (voir [`agents/personas/objectif.md`](../agents/personas/objectif.md)).

---

## 9. Dépannage

| Problème | Solution |
|---|---|
| `kimagent fetch` échoue | Vérifiez la connexion (VPN/proxy), puis `kimagent auth` ; testez `--demo` |
| « Authentification incomplète » | Relancez `kimagent auth` ; vérifiez que la boutique est active |
| Le cerveau ne répond pas | Vérifiez la clé dans `.env` ; testez `KIMAGENT_BRAIN=none` |
| Résultats approximatifs | Les données sont du 12 h max — faites `kimagent fetch --force` avant les décisions |
| Limite MCP dépassée | 60 req/min — attendez, ou réglez `KIMAGENT_DATA_MAX_AGE_H` |

---

## 10. Sécurité

- Le MCP Chariow est **en lecture seule** — aucun risque de modification.
- Jetons OAuth et données client : locaux, `.gitignore`-és, jamais commités.
- Révoquez un accès : `app.chariow.com` → **Paramètres → API Keys**.
- Relisez toujours les livrables générés avant publication (montants, prix).

## 11. Ressources officielles Chariow

- Documentation développeur : <https://chariow.dev>
- MCP : <https://chariow.dev/en/mcp/overview> · Setup : <https://chariow.dev/en/mcp/setup>
- API : <https://chariow.dev/api-reference/introduction>
- Communauté : <https://hub.chariow.com> · Aide : <https://help.chariow.com>
