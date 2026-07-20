"""Smoke test: aegisScout --help exits 0 and mentions aegisScout."""

import pytest
from typer.testing import CliRunner

from aegisScout.main import app


def test_help_exits_zero():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, f"--help exited with {result.exit_code}; output:\n{result.output}"


def test_help_mentions_aegisScout():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    combined = (result.output or "") + (getattr(result, "stderr", None) or "")
    assert "aegisScout" in combined, (
        f"--help output should mention 'aegisScout'. Got:\n{combined}"
    )


def test_version_command_works():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0, f"version exited {result.exit_code}; output:\n{result.output}"
    combined = (result.output or "") + (getattr(result, "stderr", None) or "")
    assert "aegisScout" in combined
    assert "0.1.0" in combined  # current __version__


def test_docs_subcommand_present():
    runner = CliRunner()
    result = runner.invoke(app, ["docs", "--help"])
    assert result.exit_code == 0, f"docs --help exited {result.exit_code}; output:\n{result.output}"
    combined = (result.output or "") + (getattr(result, "stderr", None) or "")
    for sub in ("mod-b", "tos", "security", "architecture"):
        assert sub in combined, f"docs command list should include '{sub}'"
