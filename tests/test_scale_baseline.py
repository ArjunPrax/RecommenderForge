from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.scale import ScaleArtifactAdapter
from tiktok_ml_agent.scale_baseline import fit_streaming_popularity


class StreamingPopularityTests(unittest.TestCase):
    def test_uses_training_labels_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            header = "user_id,video_id,date,time_ms,long_view,duration_ms,tab\n"
            (data / "log_standard_4_08_to_4_21_1k.csv").write_text(header + "u,v,20220408,1,1,10,0\nu,v,20220408,2,1,10,0\nu,x,20220408,3,0,10,0\n", encoding="utf-8")
            (data / "log_standard_4_22_to_5_08_1k.csv").write_text(header + "u,v,20220429,3,SECRET,10,0\n", encoding="utf-8")
            model = fit_streaming_popularity(ScaleArtifactAdapter("1k", data))
            self.assertGreater(model.score("v"), 0)
            self.assertLess(model.score("new"), model.score("v"))


if __name__ == "__main__":
    unittest.main()
