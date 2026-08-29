"""Tests de l'interface graphique web (Flask) — mode démo, sans réseau."""

import time
import unittest

from kimagent.gui import create_app


def _wait_done(client, run_id, timeout_s=60):
    for _ in range(int(timeout_s / 0.2)):
        st = client.get(f"/api/run/{run_id}?since=0").get_json()
        if st["status"] != "running":
            return st
        time.sleep(0.2)
    raise AssertionError(f"Délai dépassé, statut : {st}")


class TestGuiPages(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_pages_200(self):
        for path in ["/", "/agents", "/executer", "/outputs", "/rapport", "/objectif", "/healthz"]:
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_dashboard_demo(self):
        self.assertEqual(self.client.post("/api/demo").status_code, 200)
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("FormationPro", html)
        self.assertIn("démonstration", html)

    def test_personas_listed(self):
        html = self.client.get("/agents").get_data(as_text=True)
        for pid in ("marketing", "ventes", "produit", "finance", "support", "objectif"):
            self.assertIn(pid, html)

    def test_executer_prefill(self):
        html = self.client.get("/executer?persona=finance").get_data(as_text=True)
        self.assertIn('value="finance" selected', html)

    def test_unknown_run_rejected(self):
        r = self.client.post("/api/run", json={"persona": "inexistant"})
        self.assertEqual(r.status_code, 400)

    def test_path_traversal_blocked(self):
        r = self.client.get("/outputs/view/%2e%2e/%2e%2e/etc/passwd/x")
        self.assertEqual(r.status_code, 404)

    def test_ollama_endpoint(self):
        d = self.client.get("/api/ollama").get_json()
        self.assertIn("ok", d)
        self.assertIn("url", d)
        self.assertIn("models", d)


class TestGuiRun(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.client.post("/api/demo")

    def test_run_demo_no_brain(self):
        r = self.client.post("/api/run", json={
            "persona": "support", "tasks": ["paniers", "reactivation"],
            "demo": True, "no_brain": True,
        })
        self.assertEqual(r.status_code, 200)
        st = _wait_done(self.client, r.get_json()["run_id"])
        self.assertEqual(st["status"], "done")
        self.assertEqual(len(st["written"]), 2)
        self.assertGreater(st["total"], 0)  # journal capturé
        # Consultation du livrable généré
        w = st["written"][0]
        self.assertEqual(self.client.get(w["url"]).status_code, 200)
        dl = self.client.get(
            f"/outputs/download/{w['persona']}/{w['date']}/{w['name']}"
        )
        self.assertEqual(dl.status_code, 200)

    def test_utils_restored_after_run(self):
        from kimagent import brain, utils

        r = self.client.post("/api/run", json={
            "persona": "marketing", "tasks": ["posts"],
            "demo": True, "no_brain": True,
        })
        _wait_done(self.client, r.get_json()["run_id"])
        self.assertEqual(utils.step.__name__, "step")
        self.assertEqual(brain.err.__name__, "err")

    def test_parallel_runs(self):
        ids = []
        for persona, task in (("ventes", "diagnostic"), ("marketing", "posts")):
            r = self.client.post("/api/run", json={
                "persona": persona, "tasks": [task],
                "demo": True, "no_brain": True,
            })
            ids.append(r.get_json()["run_id"])
        for rid in ids:
            st = _wait_done(self.client, rid)
            self.assertEqual(st["status"], "done")


if __name__ == "__main__":
    unittest.main()
