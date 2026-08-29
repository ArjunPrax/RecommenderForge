from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class RepositorySafetyTests(unittest.TestCase):
    def test_organizer_starter_kit_is_unconditionally_ignored(self) -> None:
        """A future broad add cannot publish the unlicensed organizer kit by accident."""
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "kuairand-starter-kit/evaluate.py"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
