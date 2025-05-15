"""LeanTool public API.

This lightweight shim just re-exports the helper routines implemented in
`leanmcp.py` so that external callers can do

    import leantool
    leantool.check_lean_code(...)

without importing from private modules.
"""

from __future__ import annotations

from typing import Any, Dict

# NOTE: `leanmcp` lives at the project root.  Because the package itself is
# top-level (`leantool`), we can import it with an absolute import.
from leanmcp import check_lean_code as _check_lean_code  # type: ignore

__all__ = [
    "check_lean_code",
]


def check_lean_code(code: str, json_output: bool = False) -> Dict[str, Any]:  # noqa: D401
    """Send Lean code to the Lean executable and return the result.

    This is a simple re-export to keep the public interface stable while the
    internals evolve.
    """

    return _check_lean_code(code, json_output)
