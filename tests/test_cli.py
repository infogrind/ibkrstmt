"""CLI wiring tests: argument parsing, config loading, exit codes, messages.

Every test runs under the ``fake_home`` fixture, so the default
``~/Downloads`` / ``~/Private/finance/IBKR`` resolve into tmp_path and the
real machine is never touched.
"""

from pathlib import Path

import pytest

from ibkrstmt import cli

from .conftest import touch_all, write_config

# Captured before the autouse stub below replaces it, for the two tests
# that exercise the real Finder call.
_real_open_directory = cli._open_directory


@pytest.fixture(autouse=True)
def opened(monkeypatch) -> list[Path]:
    """Stub out the Finder call; records the directories it would have opened."""
    calls: list[Path] = []
    monkeypatch.setattr(cli, "_open_directory", calls.append)
    return calls


@pytest.fixture
def dirs(fake_home) -> tuple[Path, Path]:
    source = fake_home / "Downloads"
    target = fake_home / "Private" / "finance" / "IBKR"
    source.mkdir()
    target.mkdir(parents=True)
    return source, target


def test_moves_and_renames_statements(dirs, capsys, opened):
    source, target = dirs
    touch_all(source, ["ActivityStatement.202608.pdf", "ActivityStatement.202608(1).pdf"])
    (source / "unrelated.pdf").write_bytes(b"keep")

    exit_code = cli.main([])

    assert exit_code == 0
    assert sorted(p.name for p in target.iterdir()) == [
        "ActivityStatement 202608 1.pdf",
        "ActivityStatement 202608 2.pdf",
    ]
    assert [p.name for p in source.iterdir()] == ["unrelated.pdf"]
    out = capsys.readouterr()
    assert "ActivityStatement.202608.pdf -> " in out.out
    assert "ActivityStatement 202608 2.pdf" in out.out
    assert out.err == ""
    assert opened == [target]


def test_moves_file_contents_intact(dirs):
    source, target = dirs
    (source / "ActivityStatement.202601.pdf").write_bytes(b"%PDF-1.4 fake")

    assert cli.main([]) == 0
    assert (target / "ActivityStatement 202601 1.pdf").read_bytes() == b"%PDF-1.4 fake"


def test_nothing_to_do(dirs, capsys, opened):
    source, _ = dirs
    (source / "unrelated.pdf").write_bytes(b"")

    assert cli.main([]) == 0
    assert "No activity statements found" in capsys.readouterr().out
    assert opened == []


def test_target_not_opened_when_everything_skipped(dirs, opened):
    source, target = dirs
    (source / "ActivityStatement.202608.pdf").write_bytes(b"new")
    (target / "ActivityStatement 202608 1.pdf").write_bytes(b"old")

    assert cli.main([]) == 0
    assert opened == []


def test_open_directory_runs_macos_open(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(cli.subprocess, "run", lambda *a, **kw: calls.append((a, kw)))

    _real_open_directory(tmp_path)

    assert calls == [((["open", str(tmp_path)],), {"check": False})]


def test_open_directory_warns_when_open_is_missing(monkeypatch, tmp_path, capsys):
    def missing(*a, **kw):
        raise FileNotFoundError

    monkeypatch.setattr(cli.subprocess, "run", missing)

    _real_open_directory(tmp_path)

    assert "'open' command not found" in capsys.readouterr().err


def test_existing_target_is_skipped_with_warning(dirs, capsys):
    source, target = dirs
    (source / "ActivityStatement.202608.pdf").write_bytes(b"new")
    (target / "ActivityStatement 202608 1.pdf").write_bytes(b"old")
    (source / "ActivityStatement.202607.pdf").write_bytes(b"other")

    exit_code = cli.main([])

    assert exit_code == 0
    assert (target / "ActivityStatement 202608 1.pdf").read_bytes() == b"old"
    assert (source / "ActivityStatement.202608.pdf").read_bytes() == b"new"
    # The other statement is still processed.
    assert (target / "ActivityStatement 202607 1.pdf").read_bytes() == b"other"
    err = capsys.readouterr().err
    assert "Warning: skipping ActivityStatement.202608.pdf" in err
    assert "already exists" in err
    assert "--force" in err


@pytest.mark.parametrize("flag", ["-f", "--force"])
def test_force_overwrites_existing_target(dirs, capsys, flag):
    source, target = dirs
    (source / "ActivityStatement.202608.pdf").write_bytes(b"new")
    (target / "ActivityStatement 202608 1.pdf").write_bytes(b"old")

    exit_code = cli.main([flag])

    assert exit_code == 0
    assert (target / "ActivityStatement 202608 1.pdf").read_bytes() == b"new"
    assert not (source / "ActivityStatement.202608.pdf").exists()
    assert capsys.readouterr().err == ""


def test_missing_source_dir_reports_error(fake_home, capsys):
    (fake_home / "Private" / "finance" / "IBKR").mkdir(parents=True)

    assert cli.main([]) == 1
    assert "source directory not found" in capsys.readouterr().err


def test_missing_target_dir_reports_error(fake_home, capsys):
    source = fake_home / "Downloads"
    source.mkdir()
    touch_all(source, ["ActivityStatement.202608.pdf"])

    assert cli.main([]) == 1
    assert "target directory not found" in capsys.readouterr().err
    # Nothing was moved or deleted.
    assert (source / "ActivityStatement.202608.pdf").exists()


def test_config_directories_are_used(fake_home, tmp_path, capsys):
    source = tmp_path / "custom-source"
    target = tmp_path / "custom-target"
    source.mkdir()
    target.mkdir()
    touch_all(source, ["ActivityStatement.202603(2).pdf"])
    write_config(fake_home, f'source_dir = "{source}"\ntarget_dir = "{target}"\n')

    assert cli.main([]) == 0
    assert (target / "ActivityStatement 202603 3.pdf").exists()
    assert not (fake_home / "Downloads").exists()


def test_config_loaded_from_xdg_config_home(monkeypatch, fake_home, tmp_path):
    # Exercises the real find_config_path() -> load_config() path via the
    # environment variable rather than the ~/.config fallback.
    xdg = tmp_path / "xdg-config"
    (xdg / "ibkrstmt").mkdir(parents=True)
    source = tmp_path / "src"
    target = tmp_path / "dst"
    source.mkdir()
    target.mkdir()
    (xdg / "ibkrstmt" / "config.toml").write_text(
        f'source_dir = "{source}"\ntarget_dir = "{target}"\n', encoding="utf-8"
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    touch_all(source, ["ActivityStatement.202512.pdf"])

    assert cli.main([]) == 0
    assert (target / "ActivityStatement 202512 1.pdf").exists()


def test_invalid_config_is_reported(fake_home, capsys):
    write_config(fake_home, "not [valid toml")

    assert cli.main([]) == 1
    assert "not valid TOML" in capsys.readouterr().err


def test_help_mentions_force(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    assert "--force" in capsys.readouterr().out
