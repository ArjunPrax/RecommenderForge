from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.contracts import TestAccessError
from tiktok_ml_agent.kuairand import KuaiRandPureData


class KuaiRandSafeLoaderTests(unittest.TestCase):
    def test_hidden_test_labels_are_not_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            (data / "video_features_basic_pure.csv").write_text(
                "video_id,author_id\nv1,a1\n", encoding="utf-8"
            )
            headers = ["date", "time_ms", "user_id", "video_id", "tab", "duration_ms", "long_view"]
            for name, date, label in (
                ("log_standard_4_08_to_4_21_pure.csv", "20220408", "1"),
                ("log_standard_4_22_to_5_08_pure.csv", "20220429", "SECRET_TEST_LABEL"),
            ):
                with (data / name).open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=headers)
                    writer.writeheader()
                    writer.writerow({"date": date, "time_ms": "1", "user_id": "u1", "video_id": "v1", "tab": "1", "duration_ms": "100", "long_view": label})
            loader = KuaiRandPureData(data)
            with self.assertRaises(TestAccessError):
                loader.rows("test", include_labels=True)
            with self.assertRaises(TestAccessError):
                loader.rows("valid", include_auxiliary_labels=True)
            with self.assertRaises(TestAccessError):
                loader.rows("valid", include_watch_targets=True)
            rows = loader.rows("test", include_labels=False)
            self.assertEqual(len(rows), 1)
            self.assertIsNone(rows[0].label)
