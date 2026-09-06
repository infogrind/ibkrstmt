from pathlib import Path

import pytest

from ibkrstmt.config import Config, expand_home, find_config_path, load_config
from ibkrstmt.errors import AppError


def test_missing_config_file_returns_defaults(fake_home, tmp_path):
    config = load_config(tmp_path / "does-not-exist.toml")
    assert config == Config()


def test_defaults_point_into_home(fake_home):
    config = Config()
    assert config.source_dir == fake_home / "Downloads"
    assert config.target_dir == fake_home / "Private" / "finance" / "IBKR"


def test_loads_both_settings_with_tilde_expansion(fake_home, tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('source_dir = "~/dl"\ntarget_dir = "/abs/archive"\n', encoding="utf-8")
    config = load_config(config_file)
    assert config.source_dir == fake_home / "dl"
    assert config.target_dir == Path("/abs/archive")


def test_partial_config_keeps_other_default(fake_home, tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('target_dir = "/abs/archive"\n', encoding="utf-8")
    config = load_config(config_file)
    assert config.source_dir == fake_home / "Downloads"
    assert config.target_dir == Path("/abs/archive")


def test_empty_config_returns_defaults(fake_home, tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("# nothing configured\n", encoding="utf-8")
    assert load_config(config_file) == Config()


def test_invalid_toml_raises(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("this is not [valid toml", encoding="utf-8")
    with pytest.raises(AppError, match="not valid TOML"):
        load_config(config_file)


def test_invalid_utf8_raises(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_bytes(b'source_dir = "\xff"\n')
    with pytest.raises(AppError, match="not valid UTF-8"):
        load_config(config_file)


@pytest.mark.parametrize("key", ["source_dir", "target_dir"])
def test_dir_setting_not_a_string_raises(tmp_path, key):
    config_file = tmp_path / "config.toml"
    config_file.write_text(f"{key} = 5\n", encoding="utf-8")
    with pytest.raises(AppError, match=f"{key} must be a string"):
        load_config(config_file)


@pytest.mark.parametrize("key", ["source_dir", "target_dir"])
def test_dir_setting_empty_raises(tmp_path, key):
    config_file = tmp_path / "config.toml"
    config_file.write_text(f'{key} = ""\n', encoding="utf-8")
    with pytest.raises(AppError, match=f"{key} must not be empty"):
        load_config(config_file)


def test_unknown_setting_raises(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('source_directory = "~/Downloads"\n', encoding="utf-8")
    with pytest.raises(AppError, match="unknown setting.*source_directory"):
        load_config(config_file)


def test_expand_home_only_expands_leading_tilde(fake_home):
    assert expand_home("~/x/y") == fake_home / "x" / "y"
    assert expand_home("~") == fake_home
    assert expand_home("/a/~/b") == Path("/a/~/b")
    assert expand_home("relative/path") == Path("relative/path")


# --- find_config_path(): the XDG fallback rules are the part most likely
# to be subtly wrong, so each branch gets its own test.


def test_find_config_path_defaults_to_dot_config(fake_home):
    assert find_config_path() == fake_home / ".config" / "ibkrstmt" / "config.toml"


def test_find_config_path_honors_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert find_config_path() == tmp_path / "xdg" / "ibkrstmt" / "config.toml"


def test_find_config_path_ignores_empty_xdg_config_home(monkeypatch, fake_home):
    monkeypatch.setenv("XDG_CONFIG_HOME", "")
    assert find_config_path() == fake_home / ".config" / "ibkrstmt" / "config.toml"


def test_find_config_path_ignores_relative_xdg_config_home(monkeypatch, fake_home):
    # Per spec: a relative $XDG_CONFIG_HOME must be ignored, not resolved
    # relative to cwd.
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/path")
    assert find_config_path() == fake_home / ".config" / "ibkrstmt" / "config.toml"
