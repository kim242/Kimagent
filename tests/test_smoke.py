"""Tests de fumée Kimagent (mode démo, sans réseau, sans clé API)."""

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


if __name__ == "__main__":
    unittest.main()
