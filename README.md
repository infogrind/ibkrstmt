# ibkrstmt

Move Interactive Brokers activity statements out of your Downloads
directory into an archive, renaming them on the way.

Interactive Brokers names every download `ActivityStatement.YYYYMM.pdf`,
and the browser turns repeated downloads of the same month into
`ActivityStatement.YYYYMM(1).pdf`, `(2)`, and so on. `ibkrstmt` finds all
such files, moves them to the archive directory and renames them:

| Downloaded as | Archived as |
| --------------------------------- | -------------------------------- |
| `ActivityStatement.202608.pdf` | `ActivityStatement 202608 1.pdf` |
| `ActivityStatement.202608(1).pdf` | `ActivityStatement 202608 2.pdf` |

Existing files in the archive are never overwritten; a warning is printed
instead. Pass `-f` / `--force` to overwrite. After moving at least one
file, the archive directory is opened in Finder (via `open`).

## Usage

```
ibkrstmt [-f | --force]
```

## Configuration

`~/.config/ibkrstmt/config.toml` (or `$XDG_CONFIG_HOME/ibkrstmt/config.toml`),
both keys optional:

```toml
source_dir = "~/Downloads"
target_dir = "~/Private/finance/IBKR"
```

Both directories must already exist.

## Development

```
uv sync
uv run pytest
uv run ruff check .
```
