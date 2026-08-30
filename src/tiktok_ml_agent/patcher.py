"""Validate candidate code diffs before they enter an isolated worktree."""

from __future__ import annotations

import re
from pathlib import PurePosixPath


class PatchPolicyError(ValueError):
    """A candidate diff reaches outside its approved modification boundary."""


_DIFF_PATH = re.compile(r"^diff --git a/(.+) b/(.+)$")


def changed_paths(patch: str) -> tuple[str, ...]:
    """Return normalized changed paths from a conventional unified Git diff."""
    paths: list[str] = []
    for line in patch.splitlines():
        match = _DIFF_PATH.match(line)
        if match:
            paths.extend(match.groups())
    if not paths and patch.strip():
        raise PatchPolicyError("candidate patch must be a unified Git diff")
    normalized: list[str] = []
    for path in paths:
        candidate = PurePosixPath(path)
        if candidate.is_absolute() or ".." in candidate.parts or ".git" in candidate.parts:
            raise PatchPolicyError(f"unsafe patch path: {path}")
        normalized.append(candidate.as_posix())
    return tuple(dict.fromkeys(normalized))


def validate_patch(patch: str, allowed_paths: tuple[str, ...]) -> tuple[str, ...]:
    """Reject binary/unscoped changes and return their declared paths.

    Empty diffs are permitted for configuration-only experiments.  A planner may
    describe a code change, but it cannot widen its own allowed path boundary.
    """
    if "GIT binary patch" in patch or "Binary files " in patch:
        raise PatchPolicyError("binary candidate patches are prohibited")
    paths = changed_paths(patch)
    if not paths:
        return paths
    if not allowed_paths:
        raise PatchPolicyError("code changes require explicit allowed paths")
    normalized_prefixes = tuple(prefix.rstrip("/") + "/" for prefix in allowed_paths)
    for path in paths:
        if not any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in normalized_prefixes):
            raise PatchPolicyError(f"candidate path outside approved boundary: {path}")
    return paths
