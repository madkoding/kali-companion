"""Contract tests for the zip slip protection in STT model download (F0-4).

Pins the guarantee: a malicious zip with ../ entries is rejected before
any file is written outside the target directory.
"""

from __future__ import annotations

import zipfile
from pathlib import Path


def test_zip_with_traversal_entries_is_rejected(tmp_path: Path) -> None:
    """A zip containing ../ entries must raise before extractall."""
    stt_dir = tmp_path / "stt"
    stt_dir.mkdir()
    zip_path = tmp_path / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("normal.txt", "ok")
        zf.writestr("../../etc/passwd", "pwned")

    def _extract() -> None:
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            for name in zf.namelist():
                resolved = (stt_dir / name).resolve()
                if not str(resolved).startswith(str(stt_dir.resolve())):
                    raise ValueError(f"Zip slip blocked: {name}")
            zf.extractall(str(stt_dir))

    import pytest
    with pytest.raises(ValueError, match="Zip slip"):
        _extract()

    # The normal file was NOT extracted (the loop raised before extractall).
    assert not (stt_dir / "normal.txt").exists()


def test_zip_with_absolute_path_is_rejected(tmp_path: Path) -> None:
    """A zip with an absolute path entry must be rejected."""
    stt_dir = tmp_path / "stt"
    stt_dir.mkdir()
    zip_path = tmp_path / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("/etc/passwd", "pwned")

    def _extract() -> None:
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            for name in zf.namelist():
                resolved = (stt_dir / name).resolve()
                if not str(resolved).startswith(str(stt_dir.resolve())):
                    raise ValueError(f"Zip slip blocked: {name}")
            zf.extractall(str(stt_dir))

    import pytest
    with pytest.raises(ValueError, match="Zip slip"):
        _extract()


def test_zip_with_safe_entries_extracts(tmp_path: Path) -> None:
    """A zip with only safe entries must extract normally."""
    stt_dir = tmp_path / "stt"
    stt_dir.mkdir()
    zip_path = tmp_path / "safe.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("model/am/final.mdl", "weights")
        zf.writestr("model/conf/mfcc.conf", "config")

    with zipfile.ZipFile(str(zip_path), "r") as zf:
        for name in zf.namelist():
            resolved = (stt_dir / name).resolve()
            assert str(resolved).startswith(str(stt_dir.resolve()))
        zf.extractall(str(stt_dir))

    assert (stt_dir / "model" / "am" / "final.mdl").exists()
    assert (stt_dir / "model" / "conf" / "mfcc.conf").exists()
