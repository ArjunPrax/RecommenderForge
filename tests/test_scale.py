from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.contracts import TestAccessError
from tiktok_ml_agent.scale import ScaleArtifactAdapter


class ScaleAdapterTests(unittest.TestCase):
    def test_test_rows_are_feature_only_and_preflight_counts_splits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            (data / "log_standard_4_08_to_4_21_1k.csv").write_text("user_id,video_id,date,time_ms,long_view,duration_ms,tab\nu,v,20220408,1,1,10,0\n", encoding="utf-8")
            (data / "log_standard_4_22_to_5_08_1k.csv").write_text("user_id,video_id,date,time_ms,long_view,duration_ms,tab\nu,v,20220429,2,SECRET,10,0\n", encoding="utf-8")
            adapter = ScaleArtifactAdapter("1k", data)
            self.assertEqual(next(adapter.iter_rows("test"))["long_view"], None)
            with self.assertRaises(TestAccessError): list(adapter.iter_rows("test", include_labels=True))
            self.assertEqual(adapter.preflight()["split_counts"], {"train": 1, "valid": 0, "test": 1})


if __name__ == "__main__":
    unittest.main()
