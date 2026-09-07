"""Compile gate: every module in quant/ and backend/ must be valid Python.

This does NOT import or execute the modules (many quant scripts have
top-level demo code); it only proves they parse and compile, which catches
syntax rot in CI without side effects.
"""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCES = sorted(REPO_ROOT.glob("quant/**/*.py")) + sorted(REPO_ROOT.glob("backend/*.py"))

assert SOURCES, "no Python sources found — repo layout broken?"


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_module_compiles(path: Path) -> None:
    py_compile.compile(str(path), doraise=True)
