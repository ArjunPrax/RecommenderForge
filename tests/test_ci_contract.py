from __future__ import annotations

import unittest
from pathlib import Path


class ContinuousIntegrationContractTests(unittest.TestCase):
    def test_integrity_workflow_runs_the_locked_data_free_suite(self) -> None:
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "integrity.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("uv sync --locked", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("git diff --check", workflow)
        self.assertIn("public-checkout test suite", workflow)


if __name__ == "__main__":
    unittest.main()
