from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tiktok_ml_agent.benchmark import load_organizer_evaluator
from tiktok_ml_agent.contracts import TestAccessError
from tiktok_ml_agent.scale import ScaleArtifactAdapter
from tiktok_ml_agent.scale_baseline import ScaleResumeMismatch, fit_hashed_streaming_popularity, fit_streaming_popularity, fit_tab_conditioned_hashed_popularity, generate_scale_submission, generate_scale_submission_resumable, load_scale_model, rescore_frozen_scale_model, save_scale_model, run_streaming_popularity, score_scale_validation_resumable


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

    def test_frozen_scale_model_generates_feature_only_submission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            header = "user_id,video_id,date,time_ms,long_view,duration_ms,tab\n"
            (data / "log_standard_4_08_to_4_21_1k.csv").write_text(header + "u,v,20220408,1,1,10,0\n", encoding="utf-8")
            (data / "log_standard_4_22_to_5_08_1k.csv").write_text(header + "u,v,20220429,2,SECRET,10,0\n", encoding="utf-8")
            model = fit_hashed_streaming_popularity(ScaleArtifactAdapter("1k", data), bits=12)
            checkpoint = save_scale_model(model, data / "model.npz")
            self.assertAlmostEqual(load_scale_model(checkpoint).score("v"), model.score("v"))
            output = data / "submission.csv"
            result = generate_scale_submission(model_path=checkpoint, variant="1k", data_dir=data, output_path=output)
            self.assertEqual(result["rows"], 1.0)
            self.assertEqual(output.read_text(encoding="utf-8").splitlines()[0], "row_id,user_id,video_id,score")
            self.assertFalse((data / "submission.csv.partial").exists())

    def test_frozen_tab_model_can_be_rescored_without_refitting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            header = "user_id,video_id,date,time_ms,long_view,duration_ms,tab\n"
            (data / "log_standard_4_08_to_4_21_1k.csv").write_text(header + "u,a,20220408,1,1,10,0\nu,b,20220408,2,0,10,1\n", encoding="utf-8")
            (data / "log_standard_4_22_to_5_08_1k.csv").write_text(header + "u,a,20220422,1,1,10,0\nu,b,20220422,2,0,10,1\n", encoding="utf-8")
            model = fit_tab_conditioned_hashed_popularity(ScaleArtifactAdapter("1k", data), bits=12, item_weight=0.5)
            checkpoint = save_scale_model(model, data / "model.npz")
            root = Path(__file__).resolve().parents[1]
            result = rescore_frozen_scale_model(model_path=checkpoint, variant="1k", data_dir=data, evaluator_path=root / "kuairand-starter-kit/evaluate.py", item_weight=0.25, shards=2)
            self.assertEqual(result["item_weight"], 0.25)

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


HEADER = "user_id,video_id,date,time_ms,long_view,duration_ms,tab\n"
EVALUATOR = Path(__file__).resolve().parents[1] / "kuairand-starter-kit/evaluate.py"


def _fixture(directory: Path) -> Path:
    """A 1K-shaped artifact with several checkpoint boundaries per split.

    Test rows carry a poisoned label so any accidental label read is loud, and
    validation rows span two users so cross-shard aggregation is exercised.
    """
    train = "".join(f"u{index % 3},v{index % 4},20220408,{index},{index % 2},10,{index % 2}\n" for index in range(12))
    valid = "".join(f"u{index % 2},v{index % 4},20220422,{index},{index % 2},10,{index % 2}\n" for index in range(12))
    test = "".join(f"u{index % 2},v{index % 4},20220429,{index},SECRET,10,{index % 2}\n" for index in range(12))
    (directory / "log_standard_4_08_to_4_21_1k.csv").write_text(HEADER + train, encoding="utf-8")
    (directory / "log_standard_4_22_to_5_08_1k.csv").write_text(HEADER + valid + test, encoding="utf-8")
    return directory


def _frozen_model(data: Path, name: str = "model.npz", item_weight: float = 0.5) -> Path:
    model = fit_tab_conditioned_hashed_popularity(ScaleArtifactAdapter("1k", data), bits=12, item_weight=item_weight)
    return save_scale_model(model, data / name)


class _StopAt:
    """Raise at a chosen checkpoint so interruption is deterministic."""

    def __init__(self, stage: str, shards_completed: int | None = None) -> None:
        self.stage = stage
        self.shards_completed = shards_completed
        self.fired = False

    def __call__(self, progress) -> None:
        if progress.stage != self.stage or self.fired:
            return
        if self.shards_completed is not None and progress.shards_completed != self.shards_completed:
            return
        self.fired = True
        raise RuntimeError("simulated interruption")


class ScaleOutputResumeTests(unittest.TestCase):
    def test_interrupted_output_resumes_to_an_identical_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            reference = generate_scale_submission_resumable(
                model_path=model, variant="1k", data_dir=data,
                output_path=data / "reference.csv", state_path=None,
            )

            hook = _StopAt("stream")
            with self.assertRaises(RuntimeError):
                generate_scale_submission_resumable(
                    model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                    state_path=data / "progress.json", checkpoint_every=5, progress_hook=hook,
                )
            self.assertTrue(hook.fired)
            self.assertFalse((data / "out.csv").exists())
            self.assertTrue((data / "out.csv.partial").exists())
            self.assertEqual(json.loads((data / "progress.json").read_text(encoding="utf-8"))["rows_completed"], 5)

            resumed = generate_scale_submission_resumable(
                model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                state_path=data / "progress.json", checkpoint_every=5,
            )
            self.assertEqual(resumed["resumed_from_row"], 5.0)
            self.assertEqual(resumed["rows"], reference["rows"])
            self.assertEqual(resumed["output_sha256"], reference["output_sha256"])
            self.assertEqual((data / "out.csv").read_bytes(), (data / "reference.csv").read_bytes())
            # Atomic publication is preserved across the resume boundary.
            self.assertFalse((data / "out.csv.partial").exists())

    def test_resume_discards_bytes_written_after_the_last_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            reference = generate_scale_submission_resumable(
                model_path=model, variant="1k", data_dir=data,
                output_path=data / "reference.csv", state_path=None,
            )
            with self.assertRaises(RuntimeError):
                generate_scale_submission_resumable(
                    model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                    state_path=data / "progress.json", checkpoint_every=5, progress_hook=_StopAt("stream"),
                )
            # Simulate a torn write: real crashes land between checkpoints.
            with (data / "out.csv.partial").open("ab") as handle:
                handle.write(b"9999,uX,vX,0.5\r\n7,")
            resumed = generate_scale_submission_resumable(
                model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                state_path=data / "progress.json", checkpoint_every=5,
            )
            self.assertEqual(resumed["output_sha256"], reference["output_sha256"])
            self.assertEqual((data / "out.csv").read_bytes(), (data / "reference.csv").read_bytes())

    def test_completed_output_state_is_reused_without_rereading_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            first = generate_scale_submission_resumable(
                model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                state_path=data / "progress.json", checkpoint_every=5,
            )
            calls: list[tuple[str, bool]] = []
            original = ScaleArtifactAdapter.iter_rows

            def spy(self, split, *, include_labels=False):
                calls.append((split, include_labels))
                return original(self, split, include_labels=include_labels)

            with mock.patch.object(ScaleArtifactAdapter, "iter_rows", spy):
                again = generate_scale_submission_resumable(
                    model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                    state_path=data / "progress.json", checkpoint_every=5,
                )
            self.assertEqual(again["resumed_stage"], "complete")
            self.assertEqual(again["output_sha256"], first["output_sha256"])
            self.assertEqual(calls, [])

    def test_output_generation_never_requests_test_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            calls: list[tuple[str, bool]] = []
            original = ScaleArtifactAdapter.iter_rows

            def spy(self, split, *, include_labels=False):
                calls.append((split, include_labels))
                return original(self, split, include_labels=include_labels)

            with mock.patch.object(ScaleArtifactAdapter, "iter_rows", spy):
                generate_scale_submission_resumable(
                    model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                    state_path=data / "progress.json", checkpoint_every=5,
                )
            self.assertEqual(calls, [("test", False)])
            self.assertNotIn("SECRET", (data / "out.csv").read_text(encoding="utf-8"))
            self.assertNotIn("SECRET", (data / "progress.json").read_text(encoding="utf-8"))
            with self.assertRaises(TestAccessError):
                next(ScaleArtifactAdapter("1k", data).iter_rows("test", include_labels=True))


class ScaleValidationResumeTests(unittest.TestCase):
    def _reference(self, data: Path, model: Path) -> dict[str, float | str]:
        return score_scale_validation_resumable(
            model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
            state_dir=data / "reference-state", shards=2,
        )

    def test_interruption_during_shard_streaming_resumes_to_identical_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            reference = self._reference(data, model)
            hook = _StopAt("stream")
            with self.assertRaises(RuntimeError):
                score_scale_validation_resumable(
                    model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                    state_dir=data / "state", shards=2, checkpoint_every=5, progress_hook=hook,
                )
            self.assertTrue(hook.fired)
            state = json.loads((data / "state/progress.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stage"], "stream")
            self.assertEqual(state["rows_completed"], 5)

            resumed = score_scale_validation_resumable(
                model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                state_dir=data / "state", shards=2, checkpoint_every=5,
            )
            self.assertEqual(resumed["resumed_from_row"], 5.0)
            for metric in ("GAUC", "nDCG@5", "primary", "users", "rows"):
                self.assertAlmostEqual(resumed[metric], reference[metric], places=12)

    def test_interruption_during_aggregation_resumes_to_identical_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            reference = self._reference(data, model)
            hook = _StopAt("aggregate", shards_completed=1)
            with self.assertRaises(RuntimeError):
                score_scale_validation_resumable(
                    model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                    state_dir=data / "state", shards=2, checkpoint_every=100, progress_hook=hook,
                )
            state = json.loads((data / "state/progress.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stage"], "aggregate")
            self.assertEqual(len(state["completed_shards"]), 1)

            resumed = score_scale_validation_resumable(
                model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                state_dir=data / "state", shards=2, checkpoint_every=100,
            )
            for metric in ("GAUC", "nDCG@5", "primary", "users", "rows"):
                self.assertAlmostEqual(resumed[metric], reference[metric], places=12)

    def test_resumable_validation_matches_the_unsharded_organizer_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model_path = _frozen_model(data)
            model = load_scale_model(model_path)
            result = score_scale_validation_resumable(
                model_path=model_path, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                state_dir=data / "state", shards=2,
            )
            adapter = ScaleArtifactAdapter("1k", data)
            users, labels, scores = [], [], []
            for row in adapter.iter_rows("valid", include_labels=True):
                users.append(str(row["user_id"]))
                labels.append(int(row["long_view"] != "0"))
                scores.append(model.score(str(row["video_id"]), str(row["tab"])))
            direct = load_organizer_evaluator(EVALUATOR)(users, labels, scores)
            self.assertAlmostEqual(result["GAUC"], direct["GAUC"])
            self.assertAlmostEqual(result["nDCG@5"], direct["nDCG@5"])
            self.assertAlmostEqual(result["primary"], direct["primary"])

    def test_validation_never_reads_the_test_split(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            calls: list[tuple[str, bool]] = []
            original = ScaleArtifactAdapter.iter_rows

            def spy(self, split, *, include_labels=False):
                calls.append((split, include_labels))
                return original(self, split, include_labels=include_labels)

            with mock.patch.object(ScaleArtifactAdapter, "iter_rows", spy):
                score_scale_validation_resumable(
                    model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                    state_dir=data / "state", shards=2,
                )
            self.assertEqual({split for split, _ in calls}, {"valid"})
            self.assertNotIn("SECRET", (data / "state/progress.json").read_text(encoding="utf-8"))

    def test_completed_validation_state_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            first = score_scale_validation_resumable(
                model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                state_dir=data / "state", shards=2,
            )
            self.assertFalse((data / "state/shards").exists())
            again = score_scale_validation_resumable(
                model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                state_dir=data / "state", shards=2,
            )
            self.assertEqual(again["resumed_stage"], "complete")
            self.assertAlmostEqual(again["primary"], first["primary"], places=12)


class ScaleResumeMismatchTests(unittest.TestCase):
    def _interrupted(self, data: Path, model: Path) -> None:
        with self.assertRaises(RuntimeError):
            generate_scale_submission_resumable(
                model_path=model, variant="1k", data_dir=data, output_path=data / "out.csv",
                state_path=data / "progress.json", checkpoint_every=5, evaluator_path=EVALUATOR,
                data_fingerprint="fingerprint-a", progress_hook=_StopAt("stream"),
            )

    def _resume(self, data: Path, **overrides):
        arguments = {
            "model_path": data / "model.npz", "variant": "1k", "data_dir": data,
            "output_path": data / "out.csv", "state_path": data / "progress.json",
            "checkpoint_every": 5, "evaluator_path": EVALUATOR, "data_fingerprint": "fingerprint-a",
        }
        arguments.update(overrides)
        return generate_scale_submission_resumable(**arguments)

    def test_rejects_a_different_frozen_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            self._interrupted(data, _frozen_model(data))
            other = _frozen_model(data, name="other.npz", item_weight=0.25)
            with self.assertRaisesRegex(ScaleResumeMismatch, r"differing fields: model_sha256$"):
                self._resume(data, model_path=other)

    def test_rejects_a_different_data_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            self._interrupted(data, _frozen_model(data))
            with self.assertRaisesRegex(ScaleResumeMismatch, r"differing fields: data_fingerprint$"):
                self._resume(data, data_fingerprint="fingerprint-b")

    def test_rejects_a_different_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            self._interrupted(data, _frozen_model(data))
            copy = data / "evaluate_copy.py"
            copy.write_text(EVALUATOR.read_text(encoding="utf-8") + "\n# revised\n", encoding="utf-8")
            with self.assertRaisesRegex(ScaleResumeMismatch, r"differing fields: evaluator_sha256$"):
                self._resume(data, evaluator_path=copy)

    def test_rejects_a_different_output_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            self._interrupted(data, _frozen_model(data))
            with self.assertRaisesRegex(ScaleResumeMismatch, r"differing fields: target$"):
                self._resume(data, output_path=data / "elsewhere.csv")

    def test_rejects_changed_source_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            self._interrupted(data, _frozen_model(data))
            log = data / "log_standard_4_22_to_5_08_1k.csv"
            log.write_text(log.read_text(encoding="utf-8") + "u9,v9,20220430,99,SECRET,10,0\n", encoding="utf-8")
            with self.assertRaisesRegex(ScaleResumeMismatch, r"differing fields: source_signature$"):
                self._resume(data)

    def test_rejects_a_changed_validation_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            with self.assertRaises(RuntimeError):
                score_scale_validation_resumable(
                    model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                    state_dir=data / "state", shards=2, checkpoint_every=5, progress_hook=_StopAt("stream"),
                )
            with self.assertRaisesRegex(ScaleResumeMismatch, r"differing fields: configuration_sha256$"):
                score_scale_validation_resumable(
                    model_path=model, variant="1k", data_dir=data, evaluator_path=EVALUATOR,
                    state_dir=data / "state", shards=4, checkpoint_every=5,
                )

    def test_resume_false_restarts_instead_of_reusing_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = _fixture(Path(directory))
            model = _frozen_model(data)
            reference = generate_scale_submission_resumable(
                model_path=model, variant="1k", data_dir=data,
                output_path=data / "reference.csv", state_path=None,
            )
            self._interrupted(data, model)
            restarted = self._resume(data, resume=False, model_path=model)
            self.assertEqual(restarted["resumed_from_row"], 0.0)
            self.assertEqual(restarted["output_sha256"], reference["output_sha256"])


if __name__ == "__main__":
    unittest.main()
