"""Tests de fumée Kimagent (mode démo, sans réseau, sans clé API)."""

import asyncio
import tempfile
import unittest
from pathlib import Path

from kimagent.brain import compact_context
from kimagent.config import Settings
from kimagent.demo_data import get_demo_data
from kimagent.personas import PERSONAS, get_persona, list_personas
from kimagent.pipeline import build_report, run_persona


class TestDemoData(unittest.TestCase):
    def setUp(self):
        self.data = get_demo_data()

    def test_structure(self):
        self.assertEqual(self.data["meta"]["source"], "demo")
        self.assertIn("get_store", self.data["tools"])
        self.assertIn("list_products", self.data["tools"])
        self.assertIn("get_sales_analytics", self.data["tools"])

    def test_store_fields(self):
        store = self.data["tools"]["get_store"]
        self.assertIn("name", store)
        self.assertIn("sales_summary", store)

    def test_context_compact(self):
        ctx = compact_context(self.data, max_chars=5000)
        self.assertIn("BOUTIQUE", ctx)
        self.assertLessEqual(len(ctx), 5000)


class TestPersonas(unittest.TestCase):
    def test_all_personas_present(self):
        self.assertGreaterEqual(len(PERSONAS), 6)
        for p in list_personas():
            self.assertTrue(p.system_prompt)
            self.assertGreaterEqual(len(p.tasks), 1)

    def test_get_persona(self):
        self.assertEqual(get_persona("marketing").name, "Contenus & Marketing")
        with self.assertRaises(KeyError):
            get_persona("inexistant")


class TestPipeline(unittest.TestCase):
    def test_run_persona_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Redirige les sorties de Kimagent vers le dossier temporaire
            from unittest import mock

            with mock.patch("kimagent.pipeline.OUTPUTS_DIR", Path(tmp)):
                written = run_persona(
                    get_persona("marketing"),
                    Settings(),
                    demo=True,
                    no_brain=True,
                )
            self.assertEqual(len(written), 4)
            for path in written:
                self.assertTrue(path.exists())
                content = path.read_text(encoding="utf-8")
                self.assertIn("PROMPT PRÊT À COPIER", content)

    def test_report(self):
        report = build_report(get_demo_data())
        self.assertIn("FormationPro Digital", report)
        self.assertIn("€", report)


class TestEbookEngine(unittest.TestCase):
    """Valide le moteur de rédaction d'e-books (découpage, comptage, assemblage)."""

    def _fake_brain(self, chapters_per_call=3, words_per_chapter=250):
        """Cerveau simulé : renvoie des chapitres génériques mais bien formés."""
        from kimagent.brain import Brain

        class FakeBrain(Brain):
            def __init__(self, settings):
                super().__init__(settings)
                self.calls = 0

            async def generate(self, system_prompt, task_prompt, context, max_tokens=4000):
                self.calls += 1
                # Extrait le nombre de chapitres demandés dans la consigne
                import re

                m = re.findall(r"## Chapitre (\d+) — (.+)", task_prompt)
                parts = ["# Mon E-book Professionnel\n\n## À propos de cet e-book\n\nIntroduction."]
                for num, title in m:
                    body = "\n\n".join(
                        f"Paragraphe {j} : contenu concret et actionnable du chapitre sur "
                        f"{title}. Étape pratique numéro {j} à appliquer immédiatement."
                        for j in range(1, 8)
                    )
                    parts.append(f"## Chapitre {num} — {title}\n\n{body}\n\n**À retenir :** l'essentiel de {title}.")
                return "\n\n".join(parts)

        return FakeBrain(Settings())

    def test_engine_writes_complete_ebook(self):
        from kimagent.ebook_engine import write_ebook
        from kimagent.personas import get_persona

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            data = get_demo_data()
            brain = self._fake_brain()
            task = get_persona("ebook").task("redaction")

            # Sans plan : le moteur doit générer via repli (8 chapitres par défaut)
            final = asyncio.run(
                write_ebook(brain, task.prompt, "contexte", out_dir / "ebook.md", out_dir, data)
            )
            self.assertTrue((out_dir / "ebook.md").exists())
            self.assertIn("# ", final)
            self.assertGreaterEqual(final.count("## Chapitre"), 6)
            self.assertGreater(brain.calls, 1)  # plusieurs lots → découpage actif
            self.assertGreater(len(final.split()), 1500)

    def test_engine_uses_existing_plan(self):
        from kimagent.ebook_engine import write_ebook
        from kimagent.personas import get_persona

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            (out_dir / "plan-ebook.md").write_text(
                "# Plan\n\n## Chapitre 1 — Découvrir\n## Chapitre 2 — Préparer\n"
                "## Chapitre 3 — Agir\n## Chapitre 4 — Accélérer\n## Chapitre 5 — Pérenniser\n"
                "## Chapitre 6 — Passer à l'échelle\n## Chapitre 7 — Éviter les erreurs\n"
                "## Chapitre 8 — Plan d'action\n",
                encoding="utf-8",
            )
            brain = self._fake_brain()
            task = get_persona("ebook").task("redaction")
            final = asyncio.run(
                write_ebook(brain, task.prompt, "contexte", out_dir / "ebook.md", out_dir, get_demo_data())
            )
            # Les titres du plan doivent apparaître dans le manuscrit
            for title in ("Découvrir", "Passer à l'échelle"):
                self.assertIn(title, final)


if __name__ == "__main__":
    unittest.main()
