"""Contract tests for the fs_read / fs_list path confinement (F0-1).

These tests pin the security guarantee: a safe tool that touches the
filesystem must NOT be able to read or list paths outside the active
profile's working_dirs. If a future refactor accidentally drops the
_is_path_allowed check, these tests fail loudly.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from kali_core.claws.base import ToolContext, ToolResult
from kali_core.claws.fs import FsListTool, FsReadTool, _is_path_allowed


def _ctx(working_dir: str, working_dirs: list[str] | None) -> ToolContext:
    return ToolContext(
        session_id="contract",
        working_dir=working_dir,
        profile="contract",
        working_dirs=working_dirs,
    )


class TestIsPathAllowed:
    def test_none_means_no_restriction(self, tmp_path: Path) -> None:
        assert _is_path_allowed(tmp_path, None) is True
        assert _is_path_allowed(tmp_path, []) is True

    def test_absolute_glob_matches_child(self, tmp_path: Path) -> None:
        child = tmp_path / "foo.txt"
        child.write_text("x")
        assert _is_path_allowed(child, [f"{tmp_path}/**"]) is True

    def test_absolute_glob_rejects_sibling(self, tmp_path: Path) -> None:
        sibling = tmp_path.parent / "bar.txt"
        sibling.write_text("x")
        assert _is_path_allowed(sibling, [f"{tmp_path}/**"]) is False

    def test_tilde_expansion(self) -> None:
        # ~/** must allow a file directly under the home directory.
        home = Path.home()
        assert _is_path_allowed(home / "anything.txt", ["~/**"]) is True

    def test_multiple_patterns_any_match(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        target = allowed / "file.txt"
        target.write_text("x")
        other = tmp_path / "other"
        other.mkdir()
        # First pattern does not match, second does.
        assert _is_path_allowed(target, [f"{other}/**", f"{allowed}/**"]) is True

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        # A pattern like /tmp/** must NOT allow /tmp_evil/x via
        # a symlink or by clever path construction.
        base = tmp_path / "sandbox"
        base.mkdir()
        evil = tmp_path / "evil"
        evil.mkdir()
        # Direct child of the sandboxed dir is allowed.
        assert _is_path_allowed(base / "in.txt", [f"{base}/**"]) is True
        # A path that is a sibling must be rejected.
        assert _is_path_allowed(evil / "secret.txt", [f"{base}/**"]) is False


class TestFsReadConfinement:
    @pytest.mark.asyncio
    async def test_rejects_path_outside_working_dirs(self, tmp_path: Path) -> None:
        # Create a file OUTSIDE the allowed dir.
        outside = tmp_path / "outside"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("TOP SECRET")

        # Only allow tmp_path/inside/**
        allowed = tmp_path / "inside"
        allowed.mkdir()
        tool = FsReadTool()
        ctx = _ctx(str(allowed), [f"{allowed}/**"])
        result = await tool.run({"path": str(secret)}, ctx)
        assert result.error is not None
        assert "not allowed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_allows_path_inside_working_dirs(self, tmp_path: Path) -> None:
        allowed = tmp_path / "inside"
        allowed.mkdir()
        f = allowed / "readable.txt"
        f.write_text("hello")
        tool = FsReadTool()
        ctx = _ctx(str(allowed), [f"{allowed}/**"])
        result = await tool.run({"path": str(f)}, ctx)
        assert result.error is None
        assert result.output["content"] == "hello"

    @pytest.mark.asyncio
    async def test_no_working_dirs_means_open(self, tmp_path: Path) -> None:
        # If the profile has no working_dirs restriction, all paths are
        # allowed (backward compat with profiles that don't set it).
        f = tmp_path / "x.txt"
        f.write_text("ok")
        tool = FsReadTool()
        ctx = _ctx(str(tmp_path), None)
        result = await tool.run({"path": str(f)}, ctx)
        assert result.error is None

    @pytest.mark.asyncio
    async def test_absolute_path_traversal_blocked(self, tmp_path: Path) -> None:
        # An LLM passes an absolute path to /etc/passwd.
        allowed = tmp_path / "sandbox"
        allowed.mkdir()
        tool = FsReadTool()
        ctx = _ctx(str(allowed), [f"{allowed}/**"])
        result = await tool.run({"path": "/etc/passwd"}, ctx)
        assert result.error is not None
        assert "not allowed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_relative_path_joined_with_working_dir(self, tmp_path: Path) -> None:
        # Relative paths are resolved against working_dir, not against
        # the LLM's CWD.
        allowed = tmp_path / "sandbox"
        allowed.mkdir()
        f = allowed / "x.txt"
        f.write_text("data")
        tool = FsReadTool()
        ctx = _ctx(str(allowed), [f"{allowed}/**"])
        result = await tool.run({"path": "x.txt"}, ctx)
        assert result.error is None
        assert result.output["content"] == "data"


class TestFsListConfinement:
    @pytest.mark.asyncio
    async def test_rejects_directory_outside_working_dirs(self, tmp_path: Path) -> None:
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "a.txt").write_text("a")
        allowed = tmp_path / "inside"
        allowed.mkdir()
        tool = FsListTool()
        ctx = _ctx(str(allowed), [f"{allowed}/**"])
        result = await tool.run({"path": str(outside)}, ctx)
        assert result.error is not None
        assert "not allowed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_allows_directory_inside_working_dirs(self, tmp_path: Path) -> None:
        allowed = tmp_path / "inside"
        allowed.mkdir()
        (allowed / "a.txt").write_text("a")
        (allowed / "b").mkdir()
        tool = FsListTool()
        ctx = _ctx(str(allowed), [f"{allowed}/**"])
        result = await tool.run({"path": str(allowed)}, ctx)
        assert result.error is None
        names = {e["name"] for e in result.output["entries"]}
        assert "a.txt" in names
        assert "b" in names
