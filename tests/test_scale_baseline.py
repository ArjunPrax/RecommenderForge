from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tiktok_ml_agent.benchmark import load_organizer_evaluator
from tiktok_ml_agent.scale import ScaleArtifactAdapter
from tiktok_ml_agent.scale_baseline import fit_hashed_streaming_popularity, fit_streaming_popularity, fit_tab_conditioned_hashed_popularity, run_streaming_popularity


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

    def test_hashed_model_is_bounded_and_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            header = "user_id,video_id,date,time_ms,long_view,duration_ms,tab\n"
            (data / "log_standard_4_08_to_4_21_1k.csv").write_text(header + "u,video,20220408,1,1,10,0\n", encoding="utf-8")
            model = fit_hashed_streaming_popularity(ScaleArtifactAdapter("1k", data), bits=12)
            self.assertEqual(len(model.totals), 4096)
            self.assertEqual(model.score("video"), model.score("video"))

    def test_tab_conditioned_model_uses_inference_known_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            header = "user_id,video_id,date,time_ms,long_view,duration_ms,tab\n"
            (data / "log_standard_4_08_to_4_21_1k.csv").write_text(
                header + "u,video,20220408,1,1,10,0\nu,video,20220408,2,0,10,1\n", encoding="utf-8"
            )
            model = fit_tab_conditioned_hashed_popularity(ScaleArtifactAdapter("1k", data), bits=12, item_weight=0.0)
            self.assertGreater(model.score("video", "0"), model.score("video", "1"))

    def test_sharded_evaluation_matches_unsharded_organizer_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            header = "user_id,video_id,date,time_ms,long_view,duration_ms,tab\n"
            (data / "log_standard_4_08_to_4_21_1k.csv").write_text(
                header + "u1,a,20220408,1,1,10,0\nu1,b,20220408,2,0,10,0\nu2,a,20220408,3,1,10,0\n",
                encoding="utf-8",
            )
            (data / "log_standard_4_22_to_5_08_1k.csv").write_text(
                header + "u1,a,20220422,1,1,10,0\nu1,b,20220422,2,0,10,0\nu2,a,20220422,3,0,10,0\nu2,b,20220422,4,1,10,0\n",
                encoding="utf-8",
            )
            root = Path(__file__).resolve().parents[1]
            result = run_streaming_popularity(
                variant="1k", data_dir=data, evaluator_path=root / "kuairand-starter-kit/evaluate.py", shards=2,
            )
            direct = load_organizer_evaluator(root / "kuairand-starter-kit/evaluate.py")(
                ["u1", "u1", "u2", "u2"], [1, 0, 0, 1], [0.8, 0.2, 0.8, 0.2],
            )
            self.assertEqual(result["rows"], 4.0)
            # u1 ranks its positive first and u2 ranks it second.  The exact
            # organizer metrics are therefore GAUC=.5 and mean nDCG=(1 +
            # 1/log2(3))/2.  This catches any incorrect cross-shard weighting.
            self.assertAlmostEqual(result["GAUC"], direct["GAUC"])
            self.assertAlmostEqual(result["nDCG@5"], direct["nDCG@5"])
            self.assertAlmostEqual(result["primary"], direct["primary"])


if __name__ == "__main__":
    unittest.main()
