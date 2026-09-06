"""Shared fixtures.

There is no file *format* to build here (the tool only looks at file
names), so the builder is a tiny helper that drops named files into a
directory and a fixture that redirects the CLI's config to a throwaway
home directory so tests never touch the real ~/Downloads or archive.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pytest


def touch_all(directory: Path, names: Iterable[str]) -> list[Path]:
    """Create empty files with the given names; returns their paths in the given order."""
    paths = []
    for name in names:
        path = directory / name
        path.write_bytes(b"")
        paths.append(path)
    return paths


@pytest.fixture
def fake_home(monkeypatch, tmp_path) -> Path:
    """Point Path.home() at tmp_path and clear $XDG_CONFIG_HOME.

    Both the XDG fallback (~/.config) and the config's own ``~`` expansion
    go through Path.home(), so this one patch isolates every path the
    tool resolves.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    return home


def write_config(home: Path, text: str) -> Path:
    config_dir = home / ".config" / "ibkrstmt"
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path
