"""Integrity checks for reusable native UI copy, not runtime acceptance."""
import json
from pathlib import Path
from string import Formatter
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Phase2CopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "ui/phase2/messages.json").read_text())
        cls.fixtures = json.loads((ROOT / "ui/phase2/scenarios.json").read_text())

    def test_translations_and_placeholders(self):
        self.assertEqual(self.catalog["source_locale"], "en")
        self.assertEqual(set(self.catalog["locales"]), {"en", "pt-BR"})
        ids = []
        for message in self.catalog["messages"]:
            with self.subTest(message=message["id"]):
                ids.append(message["id"])
                self.assertEqual(set(message["text"]), {"en", "pt-BR"})
                placeholders = []
                for locale in ("en", "pt-BR"):
                    value = message["text"][locale]
                    self.assertTrue(value.strip())
                    fields = [field for _, field, _, _ in Formatter().parse(value)
                              if field is not None]
                    self.assertTrue(all(field.isidentifier() for field in fields))
                    placeholders.append(set(fields))
                self.assertEqual(*placeholders)
        self.assertEqual(len(ids), len(set(ids)), "Duplicate semantic message ID")
        self.assertTrue({f"task.{state}" for state in (
            "queued", "planning", "running", "waiting", "completed", "failed", "canceled"
        )}.issubset(ids))

    def test_fixture_references_are_valid_and_unexecuted(self):
        self.assertEqual(self.fixtures["execution_status"], "not-run")
        self.assertEqual(self.catalog["status"], "prepared-copy-not-runtime-acceptance")
        known = {message["id"] for message in self.catalog["messages"]}
        scenarios = self.fixtures["scenarios"]
        ids = [scenario["id"] for scenario in scenarios]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate scenario ID")
        for scenario in scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(scenario["fake_inputs"])
                self.assertTrue(scenario["expected_states"])
                self.assertTrue(scenario["invariants"])
                self.assertTrue(scenario["message_ids"])
                self.assertFalse(set(scenario["message_ids"]) - known,
                                 "Scenario references missing copy")


if __name__ == "__main__":
    unittest.main()
