"""P6 (roadmap 6.4): static SQL-safety gate for the backend package.

Rule (SPEC.md "Security rules"): every ``.execute()`` / ``.executemany()``
call in ``backend/`` must use a static SQL string with bind parameters.
An f-string (``ast.JoinedStr``) as the SQL argument is only tolerated when
every interpolated value is wrapped in ``_sql_string_literal(...)`` — the
single audited escape hatch for statements that cannot take bind parameters
(DuckDB ``EXPORT DATABASE`` / ``IMPORT DATABASE`` paths; see
``backend/backup.py``).

This is intentionally a small AST scan, not a linter plugin: deterministic,
no third-party rule engine, and it fails the suite the moment anyone writes
``con.execute(f"SELECT ... {value}")`` with a raw variable.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"

_EXECUTE_METHODS = {"execute", "executemany"}


def _is_escaped_literal(node: ast.expr) -> bool:
    """True when the interpolated value is a ``_sql_string_literal(...)`` call."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_sql_string_literal"
    )


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _EXECUTE_METHODS
            and node.args
        ):
            continue
        sql = node.args[0]
        if not isinstance(sql, ast.JoinedStr):
            continue
        raw = [
            v
            for v in sql.values
            if isinstance(v, ast.FormattedValue) and not _is_escaped_literal(v.value)
        ]
        if raw:
            found.append(
                f"{path.name}:{sql.lineno} f-string SQL with raw interpolation "
                "(use bind parameters, or _sql_string_literal() for the "
                "EXPORT/IMPORT DATABASE path literals)"
            )
    return found


def test_no_raw_fstring_sql_in_backend() -> None:
    violations: list[str] = []
    for path in sorted(BACKEND_DIR.rglob("*.py")):
        violations.extend(_violations(path))
    assert violations == [], "raw string-interpolated SQL found:\n" + "\n".join(violations)


def test_sql_string_literal_escapes_quotes() -> None:
    from backend.backup import _sql_string_literal

    assert _sql_string_literal("plain") == "'plain'"
    assert _sql_string_literal("o'connor") == "'o''connor'"
    # A path that tries to break out of the literal stays inert.
    assert _sql_string_literal("x'; DROP TABLE t; --") == "'x''; DROP TABLE t; --'"
