"""A single exception type for user-facing failures.

Anything the CLI's entry point catches and prints as ``Error: {e}`` (exit
code 1, no traceback) must be an AppError: a condition the user caused and
can fix (bad config, a missing directory). Anything else is a bug and
should crash with a full traceback rather than being swallowed into a
clean-looking error message that hides what actually went wrong.
"""

from __future__ import annotations


class AppError(Exception):
    """A user-facing error: bad input, bad config, or similar -- not a bug."""
