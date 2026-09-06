"""The renaming rule for IBKR activity statement downloads.

Interactive Brokers names each download ``ActivityStatement.YYYYMM.pdf``;
the browser then disambiguates repeated downloads of the same month as
``ActivityStatement.YYYYMM(1).pdf``, ``(2)``, and so on. The archived
name replaces the dot with a space and turns the browser's zero-based,
parenthesised counter into a one-based plain number::

    ActivityStatement.202608.pdf    -> ActivityStatement 202608 1.pdf
    ActivityStatement.202608(1).pdf -> ActivityStatement 202608 2.pdf

The file extension is preserved as-is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_STATEMENT_RE = re.compile(
    r"^ActivityStatement\.(?P<period>\d{6})(?:\((?P<copy>\d+)\))?(?P<ext>\.[^.]+)$"
)


@dataclass(frozen=True, order=True)
class Statement:
    """One downloaded statement: sort key first, so a list sorts by period, then copy."""

    period: str
    number: int
    ext: str

    @property
    def archive_name(self) -> str:
        return f"ActivityStatement {self.period} {self.number}{self.ext}"


def parse_statement_name(name: str) -> Statement | None:
    """Return the parsed statement for a download filename, or None if it doesn't match."""
    match = _STATEMENT_RE.match(name)
    if match is None:
        return None
    copy = match.group("copy")
    number = 1 if copy is None else int(copy) + 1
    return Statement(period=match.group("period"), number=number, ext=match.group("ext"))


def find_statements(source_dir: Path) -> list[tuple[Path, Statement]]:
    """All matching files in source_dir, sorted by period and copy number."""
    found = []
    for entry in source_dir.iterdir():
        if not entry.is_file():
            continue
        statement = parse_statement_name(entry.name)
        if statement is not None:
            found.append((entry, statement))
    found.sort(key=lambda item: item[1])
    return found
