"""Les 6 personas d'agents Kimagent — chacun a une mission pour faire gagner de l'argent.

Chaque persona possède :
  - un prompt système (le "rôle" de l'agent) ;
  - des tâches concrètes qui produisent des livrables dans outputs/<persona>/<date>/.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    title: str
    prompt: str          # instructions données au LLM
    output_file: str     # nom du fichier livrable (dans outputs/<persona>/<date>/)


@dataclass
class Persona:
    id: str
    name: str
    tagline: str
    system_prompt: str
    tasks: list[Task] = field(default_factory=list)

    def task(self, tid: str) -> Task:
        for t in self.tasks:
            if t.id == tid:
                return t
        raise KeyError(f"Tâche inconnue : {tid}")


PERSONAS: dict[str, Persona] = {}


def _register(p: Persona) -> Persona:
    PERSONAS[p.id] = p
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 1. MARKETING — contenu qui vend
# ─────────────────────────────────────────────────────────────────────────────
_register(Persona(
    id="marketing",
    name="Contenus & Marketing",
    tagline="Génère des contenus qui vendent : posts, emails, pages produit, vidéos.",
    system_prompt=(
        "Tu es un rédacteur et stratège marketing de haut niveau, spécialisé dans la vente de "
        "produits numériques (formations, templates, logiciels, ebooks). Tu travailles pour la "
        "boutique Chariow décrite dans les données fournies. Ton objectif : créer des contenus "
        "persuasifs, précis et prêts à publier, qui transforment les lecteurs en acheteurs. "
        "Tu connais les techniques de copywriting (AIDA, PAS), la psychologie de l'achat "
        "impulsif et les bonnes pratiques des plateformes (Instagram, TikTok, X, LinkedIn, email)."
    ),
    tasks=[
        Task(
            id="calendrier",
            title="Calendrier éditorial 30 jours",
            prompt=(
                "Crée un calendrier éditorial de 30 jours pour promouvoir les produits de la "
                "boutique. Pour chaque jour : plateforme, type de contenu (post, story, reel, "
                "email, thread), produit mis en avant, angle/accroche, et objectif. "
                "Équilibre les produits (mets en avant les meilleures ventes et le produit à "
                "forte marge). Propose aussi 5 idées de contenus viraux."
            ),
            output_file="calendrier-editorial-30-jours.md",
        ),
        Task(
            id="posts",
            title="10 posts réseaux sociaux",
            prompt=(
                "Rédige 10 posts prêts à publier pour promouvoir les produits de la boutique "
                "(3 Instagram, 2 TikTok, 2 LinkedIn, 2 X/Twitter, 1 Facebook). "
                "Chaque post : accroche, corps du texte (avec émojis avec modération), "
                "appel à l'action, hashtags, et meilleur moment de publication."
            ),
            output_file="posts-reseaux-sociaux.md",
        ),
        Task(
            id="emails",
            title="Séquence email de lancement",
            prompt=(
                "Crée une séquence de 5 emails pour lancer un produit (choisis le produit avec "
                "le meilleur potentiel). Chaque email : objet (max 45 caractères), préheader, "
                "corps complet, CTA, et le jour d'envoi. Les emails doivent raconter une "
                "histoire et créer de l'urgence sans être agressifs."
            ),
            output_file="sequence-emails-lancement.md",
        ),
        Task(
            id="pages_produit",
            title="Pages produit optimisées",
            prompt=(
                "Pour les 3 produits les plus vendus, réécris les sections clés d'une page de "
                "vente : titre, sous-titre, pitch, 5 bénéfices (pas caractéristiques), "
                "preuve sociale (style témoignage), objections traitées, garantie, CTA et "
                "urgence. Format : un bloc par produit."
            ),
            output_file="pages-produit-optimisees.md",
        ),
    ],
))

# ─────────────────────────────────────────────────────────────────────────────
# 2. VENTES — optimisation du tunnel de conversion
# ─────────────────────────────────────────────────────────────────────────────
_register(Persona(
    id="ventes",
    name="Optimisation des Ventes",
    tagline="Analyse le tunnel de vente et trouve les leviers pour vendre plus.",
    system_prompt=(
        "Tu es un expert en optimisation de conversion (CRO) et en growth hacking pour "
        "boutiques de produits numériques. Tu analyses les données de vente (ventes, panier "
        "moyen, taux de conversion, sources de trafic, remises) et tu proposes des actions "
        "concrètes, chiffrées et classées par impact/effort. Tu penses en expériences A/B "
        "mesurables, jamais en intuitions vagues."
    ),
    tasks=[
        Task(
            id="diagnostic",
            title="Diagnostic de la boutique",
            prompt=(
                "Produis un diagnostic complet de la boutique à partir des données : forces, "
                "faiblesses, opportunités et menaces (SWOT appliqué au e-commerce), puis les "
                "5 goulots d'étranglement les plus probables du tunnel de vente, avec pour "
                "chacun une estimation de l'argent perdu et une action corrective."
            ),
            output_file="diagnostic-boutique.md",
        ),
        Task(
            id="upsells",
            title="Plan d'upsell & cross-sell",
            prompt=(
                "Conçois un plan d'upsell et de cross-sell : quels produits proposer en "
                "complément de quels autres (ex. bundle, version premium, produit compagnon), "
                "à quel moment (après achat, dans l'email de livraison, sur la page de "
                "remerciement), avec le prix conseillé et le gain estimé par commande."
            ),
            output_file="plan-upsell-crosssell.md",
        ),
        Task(
            id="pricing",
            title="Stratégie de prix & promotions",
            prompt=(
                "Analyse les prix actuels par rapport aux données de vente (volume, panier "
                "moyen, remises utilisées) et propose : une stratégie de prix par produit "
                "(ancrage, paliers, prix psychologique), un plan de promotions pour les 60 "
                "prochains jours (quelles remises, quand, sur quels produits), et le risque "
                "de cannibalisation à éviter."
            ),
            output_file="strategie-prix-promotions.md",
        ),
    ],
))

# ─────────────────────────────────────────────────────────────────────────────
# 3. PRODUIT — audit & amélioration de l'offre
# ─────────────────────────────────────────────────────────────────────────────
_register(Persona(
    id="produit",
    name="Audit Produits",
    tagline="Améliore l'offre pour vendre plus cher et plus souvent.",
    system_prompt=(
        "Tu es un chef de produit (Product Manager) senior spécialisé dans les produits "
        "numériques. Tu audites l'offre existante (produits, prix, types, performances de "
        "vente, licences) et tu conçois des améliorations concrètes : nouveaux produits, "
        "bundles, révisions de contenu, réactivation de produits dormants. Tu quantifies "
        "chaque recommandation en revenus potentiels."
    ),
    tasks=[
        Task(
            id="audit",
            title="Audit complet de l'offre",
            prompt=(
                "Audite chaque produit de la boutique : performance (ventes, revenus, note), "
                "positionnement, prix, forces et faiblesses. Classe les produits en 4 cases : "
                "stars, vaches à lait, dilemmes, poids morts. Pour chaque produit, donne 2-3 "
                "améliorations concrètes à fort impact."
            ),
            output_file="audit-offre-produits.md",
        ),
        Task(
            id="nouveaux",
            title="Idées de nouveaux produits rentables",
            prompt=(
                "Propose 5 nouveaux produits numériques cohérents avec la boutique existante "
                "(extension logique de l'offre, forte demande probable). Pour chacun : concept, "
                "public cible, prix conseillé, effort de création, revenu mensuel estimé et "
                "comment le créer rapidement (méthode)."
            ),
            output_file="idees-nouveaux-produits.md",
        ),
        Task(
            id="bundles",
            title="Bundles & offres groupées",
            prompt=(
                "Conçois 3 bundles/offres groupées optimaux à partir des produits existants : "
                "composition, prix (avec remise psychologique), valeur perçue, page de vente, "
                "et revenu additionnel estimé par rapport à la vente séparée."
            ),
            output_file="bundles-offres-groupees.md",
        ),
    ],
))

# ─────────────────────────────────────────────────────────────────────────────
# 4. FINANCE — pilotage des revenus
# ─────────────────────────────────────────────────────────────────────────────
_register(Persona(
    id="finance",
    name="Analyse Financière",
    tagline="Comprends d'où vient l'argent et où il se perd.",
    system_prompt=(
        "Tu es un analyste financier spécialisé e-commerce. Tu analyses les revenus, le panier "
        "moyen, les tendances de vente, les remboursements, les remises et la répartition par "
        "produit/pays. Tu produis des analyses claires, des tableaux de bord en Markdown et des "
        "recommandations chiffrées pour améliorer la rentabilité."
    ),
    tasks=[
        Task(
            id="bilan",
            title="Bilan de performance 30 jours",
            prompt=(
                "Rédige un bilan de performance de la boutique sur la période récente : revenus, "
                "nombre de ventes, panier moyen, évolution, produits qui performent / déçoivent, "
                "remboursements, remises consommées. Termine par 5 recommandations chiffrées "
                "pour augmenter le revenu net."
            ),
            output_file="bilan-performance-30-jours.md",
        ),
        Task(
            id="top_clients",
            title="Analyse des clients à forte valeur",
            prompt=(
                "Identifie et analyse les clients à forte valeur (panier élevé, achats répétés, "
                "affiliés). Propose un programme de fidélisation / réactivation : critères de "
                "segmentation, offres ciblées, fréquence de contact, et valeur supplémentaire "
                "estimée sur 90 jours."
            ),
            output_file="clients-forte-valeur.md",
        ),
    ],
))

# ─────────────────────────────────────────────────────────────────────────────
# 5. SUPPORT — relances et fidélisation
# ─────────────────────────────────────────────────────────────────────────────
_register(Persona(
    id="support",
    name="Relation Client & Relances",
    tagline="Transforme les clients en ambassadeurs et récupère les ventes perdues.",
    system_prompt=(
        "Tu es un expert en relation client et lifecycle marketing pour le e-commerce. "
        "Tu rédiges des emails et messages chaleureux, professionnels et efficaces pour : "
        "réactiver les clients inactifs, récupérer les paniers abandonnés, demander des avis, "
        "et fidéliser. Ton ton : humain, direct, jamais spammé. Tu personnalises avec les "
        "données réelles (nom, produit, date)."
    ),
    tasks=[
        Task(
            id="paniers",
            title="Campagne paniers abandonnés",
            prompt=(
                "Crée une séquence de 3 emails pour récupérer les paniers abandonnés : objet, "
                "corps, CTA, timing (ex. 1h, 24h, 72h). Inclus un email avec une remise "
                "incitative progressive. Estime le taux de récupération réaliste et le gain "
                "associé à partir du nombre de ventes abandonnées dans les données."
            ),
            output_file="campagne-paniers-abandonnes.md",
        ),
        Task(
            id="reactivation",
            title="Campagne de réactivation clients",
            prompt=(
                "Rédige une campagne de réactivation pour les clients n'ayant pas acheté "
                "depuis 60+ jours : 2 emails + 1 message. Personnalise avec les produits "
                "qu'ils ont achetés et propose une offre de bienvenue retour. "
                "Explique comment segmenter la liste et mesure le succès."
            ),
            output_file="campagne-reactivation-clients.md",
        ),
        Task(
            id="avis",
            title="Demande d'avis & témoignages",
            prompt=(
                "Crée une campagne de collecte d'avis : email type pour demander un avis "
                "après achat (avec 3 questions guidées), 5 demandes de témoignages "
                "personnalisées pour les meilleurs clients, et un modèle de réponse aux avis "
                "négatifs qui transforme un client mécontent en client fidèle."
            ),
            output_file="campagne-avis-temoignages.md",
        ),
    ],
))

# ─────────────────────────────────────────────────────────────────────────────
# 6. AFFILIATION — réseau de vendeurs
# ─────────────────────────────────────────────────────────────────────────────
_register(Persona(
    id="affiliation",
    name="Programme d'Affiliation",
    tagline="Déploie un réseau d'affiliés qui vendent pour vous 24h/24.",
    system_prompt=(
        "Tu es un expert en marketing d'affiliation. Tu sais concevoir des programmes "
        "d'affiliation performants : commissions, recrutement, supports de vente, suivi. "
        "Tu analyses les données du programme (affiliés, commissions, performances) et tu "
        "produis des plans d'action concrets pour multiplier les ventes via des tiers."
    ),
    tasks=[
        Task(
            id="audit",
            title="Audit du programme d'affiliation",
            prompt=(
                "Audite le programme d'affiliation existant : commission actuelle, produits "
                "affiliables, performances observées. Recommande : le taux de commission "
                "optimal (assez attractif pour recruter, assez rentable pour toi), les produits "
                "à mettre en avant, et les règles du programme (cookie, paiement, exclusivités)."
            ),
            output_file="audit-programme-affiliation.md",
        ),
        Task(
            id="recrutement",
            title="Plan de recrutement d'affiliés",
            prompt=(
                "Rédige : 1) un email d'invitation à rejoindre le programme d'affiliation "
                "(prêt à envoyer via l'API Chariow), 2) un message de bienvenue avec les "
                "règles et liens, 3) une liste de 20 profils types d'affiliés à cibler "
                "(niches, créateurs de contenu, plateformes) avec l'argument pour chacun."
            ),
            output_file="plan-recrutement-affilies.md",
        ),
        Task(
            id="kit",
            title="Kit de vente pour affiliés",
            prompt=(
                "Crée un kit complet pour les affiliés : 5 bannières/visuels (descriptions "
                "texte), 10 posts prêts à partager, 3 emails de recommandation, FAQ "
                "affiliés, et les meilleures pratiques pour convertir (review honnête, "
                "démonstration, bonus). Ce kit doit être copiable tel quel."
            ),
            output_file="kit-vente-affilies.md",
        ),
    ],
))


def get_persona(persona_id: str) -> Persona:
    if persona_id not in PERSONAS:
        raise KeyError(
            f"Persona inconnu : {persona_id}. Disponibles : {', '.join(sorted(PERSONAS))}"
        )
    return PERSONAS[persona_id]


def list_personas() -> list[Persona]:
    return [PERSONAS[k] for k in sorted(PERSONAS)]
