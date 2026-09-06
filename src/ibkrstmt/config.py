"""User configuration, loaded per the XDG Base Directory Specification.

The config file lives at ``$XDG_CONFIG_HOME/ibkrstmt/config.toml``, falling
back to ``~/.config/ibkrstmt/config.toml`` when ``$XDG_CONFIG_HOME`` is
unset, empty, or not an absolute path (per the spec, such values must be
ignored in favor of the default).

The file has exactly two top-level keys, both optional::

    source_dir = "~/Downloads"
    target_dir = "~/Private/finance/IBKR"

A leading ``~`` is expanded to the user's home directory.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import AppError

APP_NAME = "ibkrstmt"
CONFIG_FILENAME = "config.toml"

DEFAULT_SOURCE_DIR = "~/Downloads"
DEFAULT_TARGET_DIR = "~/Private/finance/IBKR"


def expand_home(raw: str) -> Path:
    """Expand a leading ``~`` via ``Path.home()``.

    Deliberately not ``Path.expanduser()``: that reads ``$HOME`` directly,
    whereas routing through ``Path.home()`` gives tests a single seam
    (``monkeypatch.setattr(Path, "home", ...)``) that covers both the XDG
    fallback and these directory settings.
    """
    path = Path(raw)
    if path.parts and path.parts[0] == "~":
        return Path.home().joinpath(*path.parts[1:])
    return path


@dataclass
class Config:
    source_dir: Path = field(default_factory=lambda: expand_home(DEFAULT_SOURCE_DIR))
    target_dir: Path = field(default_factory=lambda: expand_home(DEFAULT_TARGET_DIR))


def find_config_path() -> Path:
    """Resolve the config file path per the XDG Base Directory spec.

    $XDG_CONFIG_HOME must be an absolute path to count; an unset, empty,
    or relative value falls back to ~/.config, per spec.
    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "")
    base = (
        Path(xdg_config_home)
        if xdg_config_home and Path(xdg_config_home).is_absolute()
        else Path.home() / ".config"
    )
    return base / APP_NAME / CONFIG_FILENAME


def _read_dir_setting(data: dict, key: str, default: str, path: Path) -> Path:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise AppError(f"config file {path}: {key} must be a string")
    if not value:
        raise AppError(f"config file {path}: {key} must not be empty")
    return expand_home(value)


def load_config(path: Path) -> Config:
    """Load and validate the config file, or return defaults if it's absent.

    Fails loudly (raising AppError) on anything present but malformed, but
    a missing file is a normal, expected case.
    """
    if not path.exists():
        return Config()

    try:
        raw = path.read_bytes()
    except OSError as e:
        raise AppError(f"could not read config file {path}: {e}") from e

    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as e:
        raise AppError(f"config file {path} is not valid UTF-8: {e}") from e
    except tomllib.TOMLDecodeError as e:
        raise AppError(f"config file {path} is not valid TOML: {e}") from e

    unknown = sorted(set(data) - {"source_dir", "target_dir"})
    if unknown:
        raise AppError(f"config file {path}: unknown setting(s): {', '.join(unknown)}")

    return Config(
        source_dir=_read_dir_setting(data, "source_dir", DEFAULT_SOURCE_DIR, path),
        target_dir=_read_dir_setting(data, "target_dir", DEFAULT_TARGET_DIR, path),
    )
