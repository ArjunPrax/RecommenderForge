from __future__ import annotations

import unittest

from tiktok_ml_agent.baseline_runner import encode_train_inference
from tiktok_ml_agent.kuairand import KuaiRandRow


def row(user: str, video: str, label: int | None) -> KuaiRandRow:
    return KuaiRandRow(20220408, 1, user, video, "a", "0", 100.0, label)


class SubmissionEncodingTests(unittest.TestCase):
    def test_inference_rows_need_no_labels(self) -> None:
        matrix, dimension = encode_train_inference(
            [row("u1", "v1", 1), row("u2", "v2", 0)], [row("u1", "v3", None)]
        )
        self.assertEqual(matrix.shape, (1, 5))
        self.assertGreater(dimension, 0)


if __name__ == "__main__":
    unittest.main()
