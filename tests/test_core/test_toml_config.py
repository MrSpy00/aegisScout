"""
Tests for the toml_config loader.

These tests cover the new frozen-mode resolution path and confirm
``load_toml_config`` correctly locates ``config/config.toml`` and
falls back to ``config.example.toml``.
"""
from pathlib import Path

import pytest

from aegisScout.core import toml_config


def test_load_toml_config_from_temp_dir(tmp_path, monkeypatch):
    """A custom config dir under a temp path is loaded correctly."""
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "config.toml").write_text(
        '[rate_limits]\nminute_limit = 7\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(toml_config, "CONFIG_DIR", cfg)
    monkeypatch.setattr(toml_config, "CONFIG_FILE", cfg / "config.toml")
    data = toml_config.load_toml_config()
    assert data["rate_limits"]["minute_limit"] == 7


def test_load_toml_config_with_explicit_path(tmp_path):
    """``load_toml_config(config_path=...)`` uses the override, not CONFIG_FILE."""
    cfg = tmp_path / "alt"
    cfg.mkdir()
    (cfg / "config.toml").write_text('foo = "bar"\n', encoding="utf-8")
    data = toml_config.load_toml_config(cfg / "config.toml")
    assert data == {"foo": "bar"}


def test_load_toml_config_missing_file_returns_empty(tmp_path, monkeypatch):
    """A non-existent config file returns {} (not raise)."""
    cfg = tmp_path / "empty_config"
    cfg.mkdir()
    monkeypatch.setattr(toml_config, "CONFIG_DIR", cfg)
    monkeypatch.setattr(toml_config, "CONFIG_FILE", cfg / "config.toml")
    assert toml_config.load_toml_config() == {}


def test_load_toml_config_falls_back_to_example(tmp_path, monkeypatch):
    """When config.toml is absent but config.example.toml exists, example is loaded."""
    cfg = tmp_path / "fb"
    cfg.mkdir()
    (cfg / "config.example.toml").write_text(
        '[x]\ny = 1\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(toml_config, "CONFIG_DIR", cfg)
    monkeypatch.setattr(toml_config, "CONFIG_FILE", cfg / "config.toml")
    data = toml_config.load_toml_config()
    assert data == {"x": {"y": 1}}


def test_resolve_config_dir_finds_real_project_config():
    """In the normal dev layout, _resolve_config_dir() finds the project-root config/."""
    resolved = toml_config._resolve_config_dir()
    # Project root contains a `config` dir with config.example.toml.
    assert resolved.exists()
    assert (resolved / "config.example.toml").exists()


def test_resolve_config_dir_env_override(monkeypatch, tmp_path):
    """$AEGISSCout_CONFIG_DIR overrides everything."""
    env_dir = tmp_path / "env_config"
    env_dir.mkdir()
    monkeypatch.setenv("AEGISSCout_CONFIG_DIR", str(env_dir))
    resolved = toml_config._resolve_config_dir()
    assert resolved == env_dir.resolve()
