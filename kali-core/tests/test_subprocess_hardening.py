"""Contract tests for run_command and run_tests subprocess hardening (F0-2, F0-3).

These tests pin two guarantees:
  1. run_command and run_tests use create_subprocess_exec (no shell),
     so shell metacharacters in the LLM's input are passed as literal
     argv elements and never interpreted.
  2. run_tests rejects paths with shell metacharacters before spawning
     the process.
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, patch

import pytest

from kali_core.claws.base import ToolContext, ToolResult
from kali_core.claws.command import RunCommandTool
from kali_core.claws.tests import RunTestsTool


def _ctx() -> ToolContext:
    return ToolContext(
        session_id="contract",
        working_dir="/tmp",
        profile="contract",
    )


class TestRunCommandNoShell:
    @pytest.mark.asyncio
    async def test_uses_subprocess_exec_not_shell(self) -> None:
        """The tool must call create_subprocess_exec, never create_subprocess_shell."""
        with patch("asyncio.create_subprocess_exec") as mock_exec, \
             patch("asyncio.create_subprocess_shell") as mock_shell:
            # Mock the process to return immediately.
            mock_proc = mock_exec.return_value
            mock_proc.communicate = AsyncMock(
                return_value=(b"hello\n", b"")
            )

            tool = RunCommandTool()
            await tool.run({"command": "echo hello", "timeout": 5}, _ctx())

            mock_exec.assert_called_once()
            # Shell must never be used.
            mock_shell.assert_not_called()
            # The first argv element must be "echo", the second "hello".
            args = mock_exec.call_args.args
            assert args[0] == "echo"
            assert args[1] == "hello"

    @pytest.mark.asyncio
    async def test_shell_metacharacters_are_literal(self) -> None:
        """A command like `echo ; rm -rf /` must NOT be interpreted by a shell.

        With create_subprocess_exec, the entire string after shlex.split
        becomes argv; the `;` is a shell construct that has no meaning
        in argv, so the resulting process will simply fail to find the
        executable `echo` (which is fine — the point is no shell ran).
        """
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock_exec.return_value
            mock_proc.communicate = AsyncMock(
                return_value=(b"", b"not found")
            )

            tool = RunCommandTool()
            await tool.run(
                {"command": "echo ; rm -rf /tmp/nonexistent", "timeout": 5},
                _ctx(),
            )

            # No shell call.
            args = mock_exec.call_args.args
            # shlex.split preserves the `;` as a literal argument.
            assert ";" in args
            # The `rm` is also a literal argument, not a separate command.
            assert "rm" in args

    @pytest.mark.asyncio
    async def test_invalid_command_rejected(self) -> None:
        tool = RunCommandTool()
        # Unmatched quote: shlex.split raises ValueError.
        result = await tool.run({"command": "echo 'unterminated"}, _ctx())
        assert result.error is not None
        assert "Invalid command" in result.error


class TestRunTestsNoShell:
    @pytest.mark.asyncio
    async def test_uses_subprocess_exec(self) -> None:
        with patch("asyncio.create_subprocess_exec") as mock_exec, \
             patch("asyncio.create_subprocess_shell") as mock_shell:
            mock_proc = mock_exec.return_value
            mock_proc.communicate = AsyncMock(
                return_value=(b"", b"")
            )
            mock_proc.returncode = 0

            tool = RunTestsTool()
            await tool.run(
                {"framework": "pytest", "timeout": 5},
                ToolContext(
                    session_id="c",
                    working_dir="/tmp",
                    profile="c",
                ),
            )

            mock_exec.assert_called_once()
            mock_shell.assert_not_called()
            # First arg must be sys.executable (the running python), not
            # the literal string "python" which may not be on PATH.
            args = mock_exec.call_args.args
            assert args[0] == sys.executable
            assert args[1] == "-m"
            assert args[2] == "pytest"

    @pytest.mark.asyncio
    async def test_rejects_path_with_shell_metacharacters(self) -> None:
        tool = RunTestsTool()
        result = await tool.run(
            {
                "framework": "pytest",
                "path": "; rm -rf /tmp/nonexistent",
                "timeout": 5,
            },
            _ctx(),
        )
        assert result.error is not None
        assert "Invalid path" in result.error

    @pytest.mark.asyncio
    async def test_rejects_path_with_command_substitution(self) -> None:
        tool = RunTestsTool()
        result = await tool.run(
            {"framework": "pytest", "path": "$(echo pwned)", "timeout": 5},
            _ctx(),
        )
        assert result.error is not None
        assert "Invalid path" in result.error

    @pytest.mark.asyncio
    async def test_rejects_path_with_backticks(self) -> None:
        tool = RunTestsTool()
        result = await tool.run(
            {"framework": "pytest", "path": "`echo pwned`", "timeout": 5},
            _ctx(),
        )
        assert result.error is not None
        assert "Invalid path" in result.error

    @pytest.mark.asyncio
    async def test_accepts_safe_path(self) -> None:
        """A normal path like tests/test_foo.py must be accepted."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock_exec.return_value
            mock_proc.communicate = AsyncMock(
                return_value=(b"", b"")
            )
            mock_proc.returncode = 0

            tool = RunTestsTool()
            result = await tool.run(
                {"framework": "pytest", "path": "tests/test_foo.py", "timeout": 5},
                _ctx(),
            )
            # No error from validation; the path appears in argv.
            assert result.error is None
            args = mock_exec.call_args.args
            assert "tests/test_foo.py" in args
