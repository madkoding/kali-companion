"""Test runner tool — run_tests.

Auto-detects the test framework from the working directory and runs the
suite. Detection order:
  1. `framework` param if provided.
  2. pyproject.toml / pytest.ini / setup.cfg with pytest config → pytest.
  3. package.json with a "test" script → npm test.
  4. go.mod → go test.
  5. Cargo.toml → cargo test.
  6. Fall back to pytest.
"""

from __future__ import annotations

import asyncio
import re
import shlex
import sys
from pathlib import Path

from .base import ToolContext, ToolResult

# ponytail: simple path validation — only allow safe characters
_SAFE_PATH_RE = re.compile(r"^[\w./\-\\]+$")


class RunTestsTool:
    name = "run_tests"
    description = (
        "Run the test suite for the project in the working directory. "
        "Auto-detects pytest, jest, go test, or cargo test."
    )
    schema = {
        "type": "object",
        "properties": {
            "framework": {
                "type": "string",
                "description": (
                    "Force a framework: pytest, jest, go, cargo. "
                    "Auto-detects if omitted."
                ),
            },
            "path": {
                "type": "string",
                "description": "Subdirectory or test file to run (optional).",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 120).",
            },
        },
        "additionalProperties": False,
    }
    risk_level = "sensitive"

    def _detect_framework(self, working_dir: str) -> str:
        """Detect the test framework from the working directory."""
        wd = Path(working_dir)

        # pytest: pyproject.toml, pytest.ini, setup.cfg, conftest.py
        if (wd / "pyproject.toml").exists() or (wd / "pytest.ini").exists():
            return "pytest"
        if (wd / "setup.cfg").exists():
            cfg = (wd / "setup.cfg").read_text(errors="replace")
            if "[tool:pytest]" in cfg or "pytest" in cfg.lower():
                return "pytest"
        if (wd / "conftest.py").exists():
            return "pytest"
        if any(wd.glob("test_*.py")) or any(wd.glob("*_test.py")):
            return "pytest"

        # jest: package.json with "test" script
        pkg = wd / "package.json"
        if pkg.exists():
            import json
            try:
                data = json.loads(pkg.read_text(errors="replace"))
                if "test" in data.get("scripts", {}):
                    return "jest"
            except (json.JSONDecodeError, KeyError):
                pass

        # go test: go.mod
        if (wd / "go.mod").exists():
            return "go"

        # cargo test: Cargo.toml
        if (wd / "Cargo.toml").exists():
            return "cargo"

        # Default: pytest
        return "pytest"

    def _build_command(self, framework: str, path: str | None) -> list[str]:
        """Build the argv list for the detected framework."""
        if framework == "pytest":
            args = [sys.executable, "-m", "pytest"]
            if path:
                args.append(path)
            args.extend(["-v", "--tb=short"])
        elif framework == "jest":
            args = ["npm", "test"]
            if path:
                args.extend(["--", path])
        elif framework == "go":
            args = ["go", "test"]
            if path:
                args.append(path)
            args.append("-v")
        elif framework == "cargo":
            args = ["cargo", "test"]
        else:
            args = [sys.executable, "-m", "pytest"]
        return args

    async def run(self, params: dict, ctx: ToolContext) -> ToolResult:
        framework = params.get("framework", "")
        path = params.get("path", "")
        timeout = int(params.get("timeout", 120))

        if not framework:
            framework = self._detect_framework(ctx.working_dir)

        if path and not _SAFE_PATH_RE.match(path):
            return ToolResult(error=f"Invalid path: {path}")

        args = self._build_command(framework, path or None)

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=ctx.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as e:
            return ToolResult(error=f"Failed to start tests: {e}")

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return ToolResult(error=f"Tests timed out after {timeout}s.")

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        return ToolResult(
            output={
                "framework": framework,
                "command": " ".join(shlex.quote(a) for a in args),
                "exit_code": proc.returncode,
                "stdout": stdout_text[:10000],
                "stderr": stderr_text[:5000],
                "passed": proc.returncode == 0,
            }
        )