"""Import-purity gate for the P7 standardized quant modules.

Every module in STANDARDIZED_MODULES must, when imported in a fresh
interpreter (so the import guard is genuinely exercised):

1. produce no stdout (no demo code runs at import time), and
2. expose the standard ``compute`` facade.

``quant.api`` is the dispatch layer: it must also import silently and expose
the five dispatch functions used by the backend analytics layer.

``tests/test_quant_compile.py`` remains the compile-only gate for the whole
``quant/`` tree; this gate is stricter and applies only to modules that have
been standardized (P7-A flagship list; P7-B extends it).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

STANDARDIZED_MODULES = [
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

DISPATCH_FUNCTIONS = [
    "compute_var",
    "compute_es",
    "compute_volatility",
    "compute_portfolio_risk",
    "compute_var_backtest",
]


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


@pytest.mark.parametrize("module", STANDARDIZED_MODULES)
def test_import_is_pure_and_exposes_compute(module: str) -> None:
    result = _import_in_subprocess(module, ["compute"])
    assert result["stdout_empty"], f"importing {module} wrote to stdout (demo code runs at import)"
    assert result["attributes"]["compute"], f"{module} does not expose the standard compute facade"


def test_dispatch_layer_import_is_pure() -> None:
    result = _import_in_subprocess("quant.api", DISPATCH_FUNCTIONS)
    assert result["stdout_empty"], "importing quant.api wrote to stdout"
    for name in DISPATCH_FUNCTIONS:
        assert result["attributes"][name], f"quant.api does not expose {name}"
