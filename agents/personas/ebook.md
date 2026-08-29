# 📚 Persona : Éditeur d'E-books

**Objectif :** rédiger des e-books professionnels qui résolvent de **vrais
problèmes** et qui **se vendent** — en s'appuyant sur ce qui marche déjà dans
votre boutique (meilleures ventes, catégories, prix, pays clients) et sur les
niches les plus rentables du marché.

## Ce que l'agent produit

| Tâche | Livrable |
|---|---|
| `analyse` | Analyse du marché + **sujet gagnant** recommandé (5 sujets classés, prix, concurrence, revenu estimé) |
| `plan` | Plan détaillé de l'e-book (titre vendeur, promesse, 8-12 chapitres, bonus, pages/prix) |
| `redaction` | **E-book complet rédigé** (4 000-8 000 mots, chapitres actionnables, modèles copiables) |
| `page_vente` | Page de vente + **fiche produit Chariow prête à créer** + posts de lancement + emails |
| `couverture` | Description détaillée de la couverture et des pages (réalisable avec Canva ou une IA d'image) |

## Les 10 niches d'e-books les plus rentables (référence marché)

1. Business en ligne & monétisation
2. Freelancing
3. Agriculture & élevage
4. Finance personnelle & épargne
5. Cuisine & nutrition
6. Santé & bien-être
7. Éducation & orientation
8. Artisanat & création
9. Technologie & numérique
10. Développement personnel

> Sources : blog officiel Chariow — « 10 meilleures niches pour vendre des
> produits digitaux en Afrique » et « 20 idées de produits digitaux rentables
> en 2026 ».

## Utilisation

### Automatique (cerveau IA configuré)

```bash
# .env : KIMAGENT_BRAIN=anthropic (ou openai, ollama)
.venv/bin/python -m kimagent run ebook                    # tout le processus
.venv/bin/python -m kimagent run ebook --tasks analyse    # juste le sujet gagnant
```

Déroulé conseillé (une session par jour) :

```bash
.venv/bin/python -m kimagent run ebook --tasks analyse    # J1 : choisir le sujet
.venv/bin/python -m kimagent run ebook --tasks plan       # J1 : valider le plan
.venv/bin/python -m kimagent run ebook --tasks redaction  # J2 : rédaction complète
.venv/bin/python -m kimagent run ebook --tasks page_vente,couverture  # J3 : vendre
```

> ℹ️ La rédaction est **longue** : le moteur Kimagent découpe l'écriture en
> lots de chapitres pour obtenir un manuscrit complet (4 000+ mots) même avec
> les limites de sortie des modèles. Plusieurs appels API sont nécessaires.

### Manuel (sans clé API)

```bash
.venv/bin/python -m kimagent run ebook --no-brain
# ou
.venv/bin/python -m kimagent prompts ebook --task redaction
```

Copiez les prompts dans Claude/ChatGPT/Cursor (connectés à Chariow), puis
collez les réponses dans `outputs/ebook/<date>/`.

## Après génération : publier sur Chariow

1. **Vérifiez et relisez** le manuscrit (`outputs/ebook/<date>/ebook-complet.md`)
   — corrigez, personnalisez (votre nom, votre marque), ajoutez des exemples
   personnels.
2. **Convertissez en PDF professionnel** : Pandoc, Google Docs, Canva, ou
   l'extension Markdown→PDF de VS Code.
3. **Créez la couverture** avec Canva (ou une IA d'image) en suivant
   `couverture-maquette.md`.
4. **Créez le produit sur Chariow** (type « downloadable ») avec la fiche
   produit de `page-vente-fiche-produit.md` : nom, description, prix conseillé,
   fichier PDF en livrable.
5. **Lancez** : posts, email à votre liste, page de vente, et proposez-le à
   vos affiliés (persona `affiliation`).

## KPI à surveiller

Ventes de l'e-book, taux de conversion de la page de vente, note/avis,
recommandations, revenu mensuel par e-book, panier moyen (e-book seul vs
e-book + produit complémentaire).
