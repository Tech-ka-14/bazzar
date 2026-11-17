"""Import-purity gate for the standardized quant library (P7).

Every module under ``quant/**`` (discovered by glob, same pattern as
``tests/test_quant_compile.py``) must, when imported in a fresh interpreter
(so the import guard is genuinely exercised):

1. import successfully,
2. produce no stdout (no demo code runs at import time), and
3. expose the standard ``compute`` facade and a module docstring.

Exceptions (no ``compute`` facade required):

* every ``__init__.py`` — package markers, no analytics surface;
* ``quant.api`` — the dispatch layer; it is asserted separately below to
  expose the dispatch functions used by the backend analytics layer.

The P7-A flagship modules (``FLAGSHIP_MODULES``) were standardized first;
they are a subset of the glob-discovered set and are pinned explicitly so a
broken glob can never silently drop them from the gate.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# P7-A flagship list: pinned subset of the glob-discovered gate below.
FLAGSHIP_MODULES = [
    "quant.risk.historical_simulation_var",
    "quant.risk.conditional_var_metrics",
    "quant.risk.normal_linear_var",
    "quant.risk.parametric_var_estimation_risk",
    "quant.risk.ewma_linear_var",
    "quant.risk.correlated_monte_carlo",
    "quant.risk.stand_alone_var",
    "quant.risk.delvar_gradient_marginal",
    "quant.risk.total_var_aggregation",
    "quant.risk.single_factor_risk_decomposition",
    "quant.risk.var_coverage_tests",
    "quant.risk.basel_regulatory_backtest",
    "quant.risk.downside_rapms",
    "quant.timeseries.ewma_variance_volatility",
    "quant.timeseries.student_t_garch",
    "quant.portfolio.classical_rapms",
    "quant.stats.ols_regression_estimation",
    "quant.copulas.archimedean_copulas",
    "quant.copulas.copula_rank_calibration",
    "quant.copulas.copula_monte_carlo_var",
]

DISPATCH_MODULE = "quant.api"
DISPATCH_FUNCTIONS = [
    "compute_var",
    "compute_es",
    "compute_volatility",
    "compute_portfolio_risk",
    "compute_var_backtest",
]


def _discover_modules() -> list[str]:
    """All importable module names under ``quant/``, sorted."""
    modules = []
    for path in sorted(REPO_ROOT.glob("quant/**/*.py")):
        if "__pycache__" in path.parts:
            continue
        modules.append(".".join(path.relative_to(REPO_ROOT).with_suffix("").parts))
    return modules


ALL_MODULES = _discover_modules()

assert ALL_MODULES, "no quant modules discovered — repo layout broken?"

# Modules exempt from the ``compute`` facade requirement (see module docstring).
NO_COMPUTE_EXEMPTIONS = {m for m in ALL_MODULES if m.endswith(".__init__")} | {DISPATCH_MODULE}


def _import_in_subprocess(module: str, attributes: list) -> dict:
    """Imports ``module`` in a fresh interpreter, capturing stdout."""
    code = (
        "import contextlib, io, json\n"
        "buf = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf):\n"
        f"    import {module} as mod\n"
        "result = {\n"
        "    'stdout_empty': buf.getvalue() == '',\n"
        f"    'attributes': {{a: hasattr(mod, a) for a in {attributes!r}}},\n"
        "    'has_docstring': bool(mod.__doc__ and mod.__doc__.strip()),\n"
        "}\n"
        "print(json.dumps(result))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_flagships_covered_by_discovery() -> None:
    """The P7-A flagship modules must all be part of the glob-discovered gate."""
    missing = [m for m in FLAGSHIP_MODULES if m not in ALL_MODULES]
    assert not missing, f"flagship modules missing from quant/ tree: {missing}"


@pytest.mark.parametrize("module", ALL_MODULES)
def test_import_is_pure_and_exposes_compute(module: str) -> None:
    result = _import_in_subprocess(module, ["compute"])
    assert result["stdout_empty"], f"importing {module} wrote to stdout (demo code runs at import)"
    assert result["has_docstring"], f"{module} is missing a module docstring"
    if module in NO_COMPUTE_EXEMPTIONS:
        return
    assert result["attributes"]["compute"], f"{module} does not expose the standard compute facade"


def test_dispatch_layer_import_is_pure() -> None:
    result = _import_in_subprocess(DISPATCH_MODULE, DISPATCH_FUNCTIONS)
    assert result["stdout_empty"], "importing quant.api wrote to stdout"
    for name in DISPATCH_FUNCTIONS:
        assert result["attributes"][name], f"quant.api does not expose {name}"
