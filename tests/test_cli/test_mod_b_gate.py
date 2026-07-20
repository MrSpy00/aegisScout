"""
Tests for the Mod B (full Instagram automation) safety gate.

When `aegisScout automate enable` is invoked WITHOUT the
`--i-understand-the-risk` flag, the CLI must:
  - Print a clear error to stderr mentioning "Meta ToS"
  - Exit with non-zero status
"""

import pytest
from typer.testing import CliRunner

from aegisScout.main import app


def test_automate_enable_without_flag_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(app, ["automate", "enable"])
    # Typer's CliRunner combines stdout/stderr into output by default;
    # check both.
    stderr = getattr(result, "stderr", None) or ""
    combined = (result.output or "") + stderr
    assert result.exit_code != 0, (
        f"automate enable (no flag) should fail. Output:\n{combined}"
    )
    assert "Meta ToS" in combined, (
        f"Error message must mention 'Meta ToS'. Got:\n{combined}"
    )


def test_automate_enable_without_flag_prints_clear_error():
    runner = CliRunner()
    result = runner.invoke(app, ["automate", "enable"])
    stderr = getattr(result, "stderr", None) or ""
    combined = (result.output or "") + stderr
    # Be specific about what the user is told
    assert "--i-understand-the-risk" in combined, (
        f"Error must mention the flag. Got:\n{combined}"
    )


def test_automate_unknown_action_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(app, ["automate", "frobnicate"])
    assert result.exit_code != 0, (
        f"Unknown action should fail. Output:\n{result.output}"
    )


def test_automate_disable_does_not_require_risk_flag():
    """`automate disable` is a safe operation and must succeed without risk flag."""
    runner = CliRunner()
    result = runner.invoke(app, ["automate", "disable"])
    assert result.exit_code == 0, (
        f"automate disable should succeed. Output:\n{result.output}"
    )
