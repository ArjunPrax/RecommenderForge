#!/usr/bin/env python3
"""Download a declared KuaiRand variant with checksum and path-safe extraction."""

from __future__ import annotations

import argparse
import hashlib
import tarfile
from pathlib import Path
from urllib.request import urlopen


VARIANTS = {
    "pure": ("KuaiRand-Pure.tar.gz", "0820331067a3784d9691136f772b35a7"),
    "1k": ("KuaiRand-1K.tar.gz", "6b0b9c8222d67fcd4c676218edca3f1f"),
    "27k": ("KuaiRand-27K.tar.gz", "3e3c799a24e2d23a4d2c757fbf9adf59"),
}
BASE_URL = "https://zenodo.org/records/10439422/files/"


def safe_extract(archive: Path, target: Path) -> None:
    with tarfile.open(archive, "r:gz") as bundle:
        target_root = target.resolve()
        for member in bundle.getmembers():
            destination = (target / member.name).resolve()
            if target_root not in destination.parents and destination != target_root:
                raise ValueError(f"archive member escapes target directory: {member.name}")
        bundle.extractall(target, filter="data")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=VARIANTS)
    parser.add_argument("--target", type=Path, default=Path("kuairand-starter-kit"))
    parser.add_argument("--downloads", type=Path, default=Path("artifacts/downloads"))
    args = parser.parse_args()
    filename, expected_md5 = VARIANTS[args.variant]
    args.downloads.mkdir(parents=True, exist_ok=True)
    archive = args.downloads / filename
    digest = hashlib.md5()
    with urlopen(BASE_URL + filename) as response, archive.open("wb") as output:  # nosec B310 - fixed Zenodo HTTPS source
        while block := response.read(1024 * 1024):
            output.write(block)
            digest.update(block)
    if digest.hexdigest() != expected_md5:
        archive.unlink(missing_ok=True)
        raise ValueError(f"MD5 mismatch for {filename}")
    safe_extract(archive, args.target)
    print(f"verified {filename} ({expected_md5}) and extracted into {args.target}")


if __name__ == "__main__":
    main()
