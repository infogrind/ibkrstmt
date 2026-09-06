"""CLI entry point: move IBKR activity statements from Downloads to the archive.

``main(argv)`` parses arguments, loads config and catches AppError; all
the real work happens in ``_run(...)``, which takes plain arguments and
returns an exit code, so tests call it without subprocesses.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .config import Config, find_config_path, load_config
from .errors import AppError
from .rename import find_statements


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ibkrstmt",
        description=(
            "Move Interactive Brokers activity statements (ActivityStatement.YYYYMM[(N)].pdf) "
            "from the source directory to the target directory, renaming them to "
            "'ActivityStatement YYYYMM N.pdf'. Both directories are set in "
            "~/.config/ibkrstmt/config.toml."
        ),
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite files that already exist in the target directory.",
    )
    return parser


def _open_directory(path: Path) -> None:
    """Reveal the directory in Finder via macOS's ``open`` command."""
    try:
        subprocess.run(["open", str(path)], check=False)
    except FileNotFoundError:
        print(f"Warning: could not open {path}: 'open' command not found", file=sys.stderr)


def _run(config: Config, force: bool) -> int:
    source_dir = config.source_dir
    target_dir = config.target_dir
    if not source_dir.is_dir():
        raise AppError(f"source directory not found: {source_dir}")
    if not target_dir.is_dir():
        raise AppError(f"target directory not found: {target_dir}")

    statements = find_statements(source_dir)
    if not statements:
        print(f"No activity statements found in {source_dir}")
        return 0

    moved = 0
    for src, statement in statements:
        dest = target_dir / statement.archive_name
        if dest.exists() and not force:
            print(
                f"Warning: skipping {src.name}: {dest} already exists (use --force to overwrite)",
                file=sys.stderr,
            )
            continue
        shutil.move(src, dest)
        print(f"{src.name} -> {dest}")
        moved += 1

    if moved:
        _open_directory(target_dir)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(find_config_path())
        return _run(config, args.force)
    except AppError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
