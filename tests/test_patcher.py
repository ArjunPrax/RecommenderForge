from __future__ import annotations

import unittest

from tiktok_ml_agent.patcher import PatchPolicyError, changed_paths, validate_patch


PATCH = """diff --git a/src/tiktok_ml_agent/model.py b/src/tiktok_ml_agent/model.py
index 1111111..2222222 100644
--- a/src/tiktok_ml_agent/model.py
+++ b/src/tiktok_ml_agent/model.py
@@ -1 +1 @@
-old
+new
"""


class PatchPolicyTests(unittest.TestCase):
    def test_approved_patch_is_accepted(self) -> None:
        self.assertEqual(
            validate_patch(PATCH, ("src/tiktok_ml_agent/",)),
            ("src/tiktok_ml_agent/model.py",),
        )

    def test_out_of_scope_patch_is_rejected(self) -> None:
        with self.assertRaises(PatchPolicyError):
            validate_patch(PATCH, ("tests/",))

    def test_parent_traversal_is_rejected(self) -> None:
        with self.assertRaises(PatchPolicyError):
            changed_paths("diff --git a/../../secret b/../../secret\n")


if __name__ == "__main__":
    unittest.main()
