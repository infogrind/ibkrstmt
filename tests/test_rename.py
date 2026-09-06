import pytest

from ibkrstmt.rename import Statement, find_statements, parse_statement_name

from .conftest import touch_all


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("ActivityStatement.202608.pdf", "ActivityStatement 202608 1.pdf"),
        ("ActivityStatement.202608(1).pdf", "ActivityStatement 202608 2.pdf"),
        ("ActivityStatement.202608(2).pdf", "ActivityStatement 202608 3.pdf"),
        ("ActivityStatement.202512(10).pdf", "ActivityStatement 202512 11.pdf"),
        ("ActivityStatement.202608.csv", "ActivityStatement 202608 1.csv"),
    ],
)
def test_archive_name(name, expected):
    statement = parse_statement_name(name)
    assert statement is not None
    assert statement.archive_name == expected


@pytest.mark.parametrize(
    "name",
    [
        "ActivityStatement 202608 1.pdf",  # already renamed
        "ActivityStatement.2026.pdf",  # period too short
        "ActivityStatement.20260801.pdf",  # period too long
        "ActivityStatement.202608",  # no extension
        "ActivityStatement.202608(a).pdf",  # non-numeric copy
        "ActivityStatement.202608 (1).pdf",  # space before counter
        "activitystatement.202608.pdf",  # wrong case
        "TradeConfirmation.202608.pdf",
        "notes.txt",
    ],
)
def test_non_matching_names(name):
    assert parse_statement_name(name) is None


def test_parsed_fields():
    assert parse_statement_name("ActivityStatement.202608(1).pdf") == Statement(
        period="202608", number=2, ext=".pdf"
    )


def test_find_statements_sorted_and_filtered(tmp_path):
    touch_all(
        tmp_path,
        [
            "ActivityStatement.202608(1).pdf",
            "notes.txt",
            "ActivityStatement.202607.pdf",
            "ActivityStatement.202608.pdf",
        ],
    )
    (tmp_path / "ActivityStatement.202609.pdf").mkdir()  # a directory, not a file

    found = find_statements(tmp_path)

    assert [path.name for path, _ in found] == [
        "ActivityStatement.202607.pdf",
        "ActivityStatement.202608.pdf",
        "ActivityStatement.202608(1).pdf",
    ]


def test_find_statements_empty_dir(tmp_path):
    assert find_statements(tmp_path) == []
