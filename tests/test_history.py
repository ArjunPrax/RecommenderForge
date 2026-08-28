from __future__ import annotations

import unittest

from tiktok_ml_agent.history import prior_long_view_buckets, prior_video_tab_buckets
from tiktok_ml_agent.kuairand import KuaiRandRow


def row(timestamp: int, label: int | None, user: str = "u") -> KuaiRandRow:
    return KuaiRandRow(timestamp // 1000, timestamp, user, "v", "a", "0", 100.0, label)


def video_tab_row(timestamp: int, label: int | None, video: str, tab: str = "0") -> KuaiRandRow:
    return KuaiRandRow(timestamp // 1000, timestamp, "u", video, "a", tab, 100.0, label)


class HistoryFeatureTests(unittest.TestCase):
    def test_train_feature_is_strictly_prior_and_validation_is_frozen(self) -> None:
        train = [row(20, 0), row(10, 1), row(30, 1)]
        valid = [row(40, 0), row(50, 1)]
        train_buckets, valid_buckets = prior_long_view_buckets(train, valid)
        self.assertEqual(train_buckets[1], "hist_count_0_rate_0")
        self.assertEqual(train_buckets[0], "hist_count_1_rate_7")
        self.assertEqual(train_buckets[2], "hist_count_2_rate_4")
        self.assertEqual(valid_buckets, ["hist_count_3_rate_5", "hist_count_3_rate_5"])

    def test_validation_labels_are_not_required_or_read(self) -> None:
        train = [row(10, 1)]
        valid = [row(20, None), row(30, None)]
        _, valid_buckets = prior_long_view_buckets(train, valid)
        self.assertEqual(valid_buckets, ["hist_count_1_rate_7", "hist_count_1_rate_7"])

    def test_video_tab_feature_is_strictly_prior_and_evaluation_is_frozen(self) -> None:
        train = [
            video_tab_row(20, 0, "v1"),
            video_tab_row(10, 1, "v1"),
            video_tab_row(30, 1, "v2", "1"),
        ]
        valid = [video_tab_row(40, None, "v1"), video_tab_row(50, None, "v2", "1")]
        train_buckets, valid_buckets = prior_video_tab_buckets(train, valid)
        self.assertEqual(train_buckets[1], "hist_count_0_rate_0")
        self.assertEqual(train_buckets[0], "hist_count_1_rate_7")
        self.assertEqual(train_buckets[2], "hist_count_0_rate_0")
        self.assertEqual(valid_buckets, ["hist_count_2_rate_4", "hist_count_1_rate_7"])


if __name__ == "__main__":
    unittest.main()
