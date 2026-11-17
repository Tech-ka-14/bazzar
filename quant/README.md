# Bazzar Quant Library — P7 Standard

`quant/` is a library of standalone quantitative-finance modules organized by
domain (`risk`, `copulas`, `timeseries`, `portfolio`, `stats`, `pricing`).
This file defines the **P7 module standard**: the contract that standardized
modules follow and that `quant/api.py` (the dispatch layer used by the
backend) relies on. P7-A standardized the ~20 flagship modules listed below;
P7-B mass-applies the same standard to the remaining modules.

## The standard

### 1. Import purity

A standardized module executes **nothing at import time** except imports,
function/class definitions and constant assignments. In particular it must
not print, draw random numbers, call `np.random.seed`, touch the filesystem,
or fit models at import.

All legacy demo/example code is moved **verbatim** under an
`if __name__ == "__main__":` guard at the bottom of the file, so running the
file as a script (`python quant/risk/foo.py`) behaves exactly as before.

### 2. Facade (`compute`)

Where the module has a natural primary computation, it exposes

```python
def compute(data, **params) -> dict: ...
```

- `data` is the primary input (usually a return series or matrix);
  scalar-input modules take their natural arguments instead.
- Returns a **plain JSON-serializable dict**: `float`, `int`, `str`, `bool`,
  lists and nested dicts only — never numpy scalars or arrays.
- Validates its inputs and raises `ValueError` with a clear message on
  bad input.
- Is **additive**: every pre-existing public function keeps its exact name
  and signature. Nothing is renamed or removed.

### 3. Docstring

Every standardized module has a module-level docstring with a one-line
purpose plus the governing formula/reference (textbook equation number where
the module derives from Alexander, *Market Risk Analysis*). Good existing
docstrings are kept, not rewritten.

## The dispatch layer (`quant/api.py`)

`quant/api.py` is the **only** surface the backend analytics layer uses for
the roadmap-7.3 endpoints. It delegates to the standardized flagship modules
and raises `KeyError` listing the available options on an unknown
method/model name.

| Function | Options | Delegates to |
| --- | --- | --- |
| `compute_var(returns, method, confidence, ...)` | `historical`, `parametric`, `montecarlo` | `risk.historical_simulation_var`, `risk.normal_linear_var`, `risk.correlated_monte_carlo` + `copulas.copula_monte_carlo_var` |
| `compute_es(returns, method, confidence, ...)` | `historical`, `parametric`, `montecarlo` | `risk.conditional_var_metrics`; closed-form normal ES; seeded simulation |
| `compute_volatility(returns, model, **params)` | `ewma`, `garch` | `timeseries.ewma_variance_volatility`, `timeseries.student_t_garch` |
| `compute_portfolio_risk(returns_df, weights, confidence)` | — | covariance of inputs + `risk.delvar_gradient_marginal` (Euler component VaR) |
| `compute_var_backtest(exceptions, n, confidence)` | count or 0/1 indicators | `risk.var_coverage_tests` (Kupiec, Christoffersen), `risk.basel_regulatory_backtest` |

Available choices are also exported as `VAR_METHODS`, `ES_METHODS` and
`VOLATILITY_MODELS` in `quant/api.py`.

## Flagship modules (P7-A)

| Module | Role |
| --- | --- |
| `risk/historical_simulation_var.py` | Historical simulation VaR (linear-interpolated empirical quantile) |
| `risk/conditional_var_metrics.py` | Historical VaR threshold + expected tail loss (ES) |
| `risk/normal_linear_var.py` | Parametric normal linear VaR (variance-covariance) |
| `risk/parametric_var_estimation_risk.py` | h-day parametric VaR scaling and standard errors |
| `risk/ewma_linear_var.py` | EWMA normal linear VaR (RiskMetrics) |
| `risk/correlated_monte_carlo.py` | Correlated normal/Student-t Monte Carlo engine (Cholesky) |
| `risk/stand_alone_var.py` | Stand-alone / undiversified / diversified VaR |
| `risk/delvar_gradient_marginal.py` | DelVaR gradient, marginal (component) and incremental VaR |
| `risk/total_var_aggregation.py` | Systematic + specific VaR aggregation |
| `risk/single_factor_risk_decomposition.py` | Single-factor systematic/specific risk split |
| `risk/var_coverage_tests.py` | Kupiec unconditional coverage + Christoffersen independence tests |
| `risk/basel_regulatory_backtest.py` | Basel traffic-light zones and capital multipliers |
| `risk/downside_rapms.py` | Sortino ratio, Kappa indices, Omega statistic (LPM-based) |
| `timeseries/ewma_variance_volatility.py` | EWMA variance recursion and current volatility |
| `timeseries/student_t_garch.py` | GARCH(1,1) likelihoods (normal + Student-t) and MLE estimation |
| `portfolio/classical_rapms.py` | Sharpe, Treynor, information ratios |
| `stats/ols_regression_estimation.py` | Simple OLS regression output |
| `copulas/archimedean_copulas.py` | Clayton/Gumbel densities, tail dependence, closed-form Kendall tau |
| `copulas/copula_rank_calibration.py` | Kendall/Spearman inversion to elliptical copula rho |
| `copulas/copula_monte_carlo_var.py` | Monte Carlo VaR from a simulated return matrix |

## How P7-B applies this

1. Read the target module; identify its demo code (unguarded executable
   statements below the function definitions).
2. Move the demo verbatim under `if __name__ == "__main__":`.
3. Add the module docstring (purpose + formula/reference) if missing.
4. Add `compute(...)` returning a JSON-serializable dict; do not touch
   existing public functions.
5. Add the module to the explicit import list in
   `tests/test_quant_import.py`.
6. If the module backs a 7.3 endpoint, wire it through `quant/api.py` only —
   never import modules directly from `backend/`.

## Tests

- `tests/test_quant_compile.py` — pre-existing compile gate (all modules).
- `tests/test_quant_import.py` — import purity gate: importing a
  standardized module must produce no stdout and expose `compute`.
- `tests/test_quant_flagship.py` — known-answer tests for the flagship
  modules (hand-computed references; `arch`/`statsmodels` where available;
  seeded Monte Carlo with tolerances).
