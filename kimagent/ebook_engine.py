"""Moteur de rédaction d'e-books : écrit le manuscrit chapitre par chapitre.

Stratégie pour obtenir un e-book professionnel et COMPLET même quand le modèle
a une limite de sortie : on découpe l'écriture en lots de chapitres, chaque
appel se voyant rappeler le plan (ou en générer un) et le début déjà écrit.
"""

from __future__ import annotations

import re

from .brain import Brain, compact_context
from .demo_data import get_demo_data
from .utils import err, info, ok, step, warn

MIN_WORDS_TARGET = 4000   # objectif minimum de mots pour un e-book pro
MIN_CHAPTERS = 6          # nombre minimum de chapitres


def count_words(text: str) -> int:
    """Compte les mots d'un texte Markdown (hors code/markup grossier)."""
    text = re.sub(r"[#>*`_\-—|]", " ", text)
    return len([w for w in re.split(r"\s+", text) if w.strip()])


def _split_chapters(text: str) -> list[str]:
    """Découpe un manuscrit en chapitres (titres ##)."""
    parts = re.split(r"(?m)^## ", text)
    return [p for p in parts if p.strip()]


def _extract_plan(plan_text: str) -> list[str]:
    """Extrait la liste des chapitres depuis un plan (titres "Chapitre N — X")."""
    found = re.findall(r"(?im)^\s*(?:#+\s*)?(?:chapitre\s*\d+|chapitre)\s*[—:-]?\s*(.+)$", plan_text)
    if found:
        return [f.strip(" .") for f in found]
    # Repli : lignes de type "1. Titre" ou "- Titre"
    found = re.findall(r"(?im)^\s*(?:\d+[.)]|[-*])\s+(.+)$", plan_text)
    return [f.strip(" .") for f in found]


def _fallback_plan() -> list[str]:
    """Plan par défaut si aucun plan n'est disponible."""
    return [
        "Comprendre le problème et définir son objectif",
        "Les fondamentaux : ce qu'il faut savoir avant de commencer",
        "Méthode étape par étape — partie 1 : préparer",
        "Méthode étape par étape — partie 2 : agir",
        "Méthode étape par étape — partie 3 : accélérer",
        "Erreurs à éviter et pièges courants",
        "Outils, modèles et ressources pratiques",
        "Votre plan d'action 7 jours pour des résultats rapides",
    ]


async def write_ebook(
    brain: Brain,
    task_prompt: str,
    context: str,
    output_path,
    out_dir,
    data: dict,
) -> str:
    """Écrit l'e-book complet. Retourne le manuscrit final.

    - S'il existe déjà un plan-ebook.md dans le dossier, il est utilisé ;
      sinon le premier appel génère aussi le plan.
    - Les chapitres sont rédigés en lots pour tenir dans la limite du modèle.
    """
    from .personas import get_persona

    persona = get_persona("ebook")

    # 1) Plan existant ? (généré par la tâche `plan` du même persona)
    plan_path = out_dir / "plan-ebook.md"
    plan_text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    chapters = _extract_plan(plan_text) if plan_text else []
    if len(chapters) < MIN_CHAPTERS:
        info("Aucun plan complet trouvé — le premier passage générera aussi le plan.")
        chapters = _fallback_plan()

    # 2) Rédaction par lots de chapitres
    batch_size = 3
    manuscript_parts: list[str] = []
    total_words = 0
    title_placeholder = ""

    for i in range(0, len(chapters), batch_size):
        batch = chapters[i : i + batch_size]
        step(f"Rédaction — chapitres {i + 1} à {i + len(batch)} / {len(chapters)}…")
        result = await brain.generate(
            system_prompt=persona.system_prompt,
            task_prompt=_batch_prompt(task_prompt, batch, i == 0, plan_text, manuscript_parts),
            context=context,
            max_tokens=6000,
        )
        if not result:
            warn(f"Aucun contenu pour le lot {i // batch_size + 1} — passage au suivant.")
            continue

        if i == 0:
            # Extrait le titre du premier passage
            m = re.search(r"(?m)^#\s+(.+)$", result)
            if m:
                title_placeholder = m.group(1).strip()

        manuscript_parts.append(result)
        total_words += count_words(result)
        info(f"→ {count_words(result)} mots ce lot (total : {total_words})")

    manuscript = "\n\n".join(p for p in manuscript_parts if p.strip())

    # 3) Vérification de la longueur
    if total_words < MIN_WORDS_TARGET:
        warn(
            f"Le manuscrit fait {total_words} mots (< {MIN_WORDS_TARGET} attendus). "
            "Un passage de complétion est lancé."
        )
        completion = await brain.generate(
            system_prompt=persona.system_prompt,
            task_prompt=(
                "Le manuscrit ci-dessous est trop court. Ajoute des sections substantielles "
                "sans répéter l'existant : approfondis les chapitres existants (nouveaux "
                "exemples, études de cas, modèles, FAQ), ou ajoute un chapitre « Questions "
                "fréquentes » et un chapitre « Ressources et prochaines étapes ». "
                "Rends uniquement les sections NOUVELLES, en Markdown, avec des titres ##.\n\n"
                f"MANUSCRIT ACTUEL :\n\n{manuscript[-12000:]}"
            ),
            context=context,
            max_tokens=6000,
        )
        if completion:
            manuscript = manuscript.rstrip() + "\n\n" + completion.strip()
            total_words = count_words(manuscript)

    # 4) Assemble et sauvegarde
    title = title_placeholder or "Votre e-book"
    header = (
        f"# {title}\n\n"
        f"*Généré par Kimagent — Éditeur d'E-books · {len(_split_chapters(manuscript))} "
        f"chapitres · ~{total_words} mots*\n\n---\n\n"
    )
    if data.get("meta", {}).get("source") == "demo":
        header += "> ⚠️ **Mode démonstration** : données fictives d'exemple. "
        header += "Lancez `kimagent fetch` pour votre vraie boutique.\n\n"
    final = header + manuscript.strip() + "\n"

    # En-tête standard si absent
    if not re.search(r"(?m)^## À propos", final):
        final = final.replace(
            "## Sommaire",
            "## À propos de cet e-book\n\n"
            "Ce guide pratique a été conçu pour vous donner des résultats concrets : "
            "étapes simples, exemples réels et modèles à copier. Lisez-le une première "
            "fois en entier, puis appliquez le plan d'action de la conclusion.\n\n"
            "## Sommaire",
            1,
        )

    output_path.write_text(final, encoding="utf-8")
    ok(f"E-book écrit : {output_path.relative_to(output_path.parents[1])} "
       f"({len(_split_chapters(final))} chapitres, ~{count_words(final)} mots)")
    return final


def _batch_prompt(task_prompt: str, batch: list[str], first: bool, plan_text: str, done: list[str]) -> str:
    """Construit la consigne pour un lot de chapitres."""
    base = (
        "Tâche : " + task_prompt + "\n\n"
        "Rédige en Markdown français, directement le contenu des chapitres demandés "
        "(pas d'introduction générale, pas de conclusion globale).\n"
        "Chaque chapitre : intro courte, sections (##, ###), listes, étapes numérotées, "
        "encadré « À retenir » en fin de chapitre, exemples concrets et modèles copiables.\n"
        "Ton : chaleureux, direct, tutoiement, phrases courtes.\n\n"
    )
    if not first and done:
        base += "Chapitres déjà rédigés (pour continuité, ne pas répéter) :\n" + "\n".join(
            d[-1500:] for d in done
        ) + "\n\n"
    if plan_text:
        base += "PLAN DE RÉFÉRENCE (suis-le) :\n" + plan_text[-6000:] + "\n\n"
    base += "CHAPITRES À RÉDIGER MAINTENANT :\n" + "\n".join(
        f"## Chapitre {i + 1} — {c}" for i, c in enumerate(batch)
    )
    return base
