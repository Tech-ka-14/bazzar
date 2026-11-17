"""Known-answer tests for the P7-A standardized flagship quant modules.

References are hand-computed closed forms (documented inline per case),
published textbook/critical values, the `arch` and `statsmodels` packages
where they overlap, and one pinned snapshot (GARCH) documented where it is
used. Monte Carlo tests are seeded and tolerance-based.
"""

import math

import numpy as np
import pytest
from scipy.stats import norm

from quant import api
from quant.copulas import archimedean_copulas, copula_monte_carlo_var, copula_rank_calibration
from quant.portfolio import classical_rapms
from quant.risk import (
    basel_regulatory_backtest,
    conditional_var_metrics,
    correlated_monte_carlo,
    delvar_gradient_marginal,
    downside_rapms,
    historical_simulation_var,
    normal_linear_var,
    parametric_var_estimation_risk,
    single_factor_risk_decomposition,
    stand_alone_var,
    total_var_aggregation,
    var_coverage_tests,
)
from quant.stats import ols_regression_estimation
from quant.timeseries import ewma_variance_volatility, student_t_garch

# 10-point hand dataset: symmetric, evenly spaced, so quantile semantics can
# be verified by hand. sorted == the array itself.
HAND_RETURNS = np.array([-0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04])


class TestHistoricalVar:
    def test_linear_quantile_semantics(self):
        # alpha = 0.1; numpy "linear" interpolation: position h = 0.1*(10-1)
        # = 0.9 -> sorted[0] + 0.9*(sorted[1]-sorted[0]) = -0.05 + 0.9*0.01
        # = -0.041, so VaR = 0.041 exactly (by hand).
        var_pct, var_val = historical_simulation_var.calculate_empirical_historical_var(
            HAND_RETURNS, 1_000_000.0, 0.90
        )
        assert var_pct == pytest.approx(0.041, abs=1e-12)
        assert var_val == pytest.approx(41_000.0, abs=1e-6)

    def test_compute_facade_matches_function(self):
        out = historical_simulation_var.compute(HAND_RETURNS, confidence=0.90, portfolio_value=2.0)
        assert out["var"] == pytest.approx(0.041, abs=1e-12)
        assert out["var_value"] == pytest.approx(0.082, abs=1e-12)
        assert out["method"] == "historical"
        assert out["n"] == 10

    def test_var_increases_with_confidence(self):
        var_95 = historical_simulation_var.compute(HAND_RETURNS, confidence=0.95)["var"]
        var_90 = historical_simulation_var.compute(HAND_RETURNS, confidence=0.90)["var"]
        assert var_95 > var_90 > 0.0


class TestHistoricalEs:
    def test_lower_quantile_and_tail_semantics(self):
        # calculate_historical_etl uses method="lower": index floor(0.9) = 0
        # -> threshold = -0.05 exactly; the tail is {r <= -0.05} = {-0.05},
        # so ETL = 0.05 exactly (by hand).
        var_value, etl_value = conditional_var_metrics.calculate_historical_etl(
            HAND_RETURNS, 0.90, 1.0
        )
        assert var_value == pytest.approx(0.05, abs=1e-12)
        assert etl_value == pytest.approx(0.05, abs=1e-12)

    def test_es_at_least_var(self):
        rng = np.random.default_rng(3)
        returns = rng.standard_t(df=4, size=500) * 0.02
        out = conditional_var_metrics.compute(returns, confidence=0.975)
        assert out["es"] >= out["var"] >= 0.0

    def test_normal_benchmark_var(self):
        # z_0.99 * 0.03 * 10_000_000 with expected active return 0
        expected = norm.ppf(0.99) * 0.03 * 10_000_000
        got = conditional_var_metrics.calculate_normal_benchmark_var(0.0, 0.03, 0.99, 10_000_000)
        assert got == pytest.approx(expected, rel=1e-12)


class TestParametricVar:
    def test_closed_form(self):
        # z_0.99 = 2.3263478740408408; VaR = z*sigma - mu
        # = 2.3263478740408408 * 0.02 - 0.001 = 0.04552695748081682 (hand).
        got = normal_linear_var.calculate_normal_var(mu=0.001, sigma=0.02, confidence_level=0.99)
        assert got == pytest.approx(0.04552695748081682, rel=1e-12)

    def test_monetary_var(self):
        got = normal_linear_var.calculate_normal_var(0.05, 0.12, 0.90, 2_000_000)
        expected = (norm.ppf(0.90) * 0.12 - 0.05) * 2_000_000
        assert got == pytest.approx(expected, rel=1e-12)

    def test_horizon_scaling(self):
        # z_0.99 * 0.20 * sqrt(10) = 1.4713115823719107 (hand).
        got = parametric_var_estimation_risk.calculate_normal_var(0.20, 10, 0.01)
        assert got == pytest.approx(1.4713115823719107, rel=1e-12)
        # sqrt-h scaling: VaR(h=4) == 2 * VaR(h=1)
        v1 = parametric_var_estimation_risk.calculate_normal_var(0.20, 1, 0.01)
        v4 = parametric_var_estimation_risk.calculate_normal_var(0.20, 4, 0.01)
        assert v4 == pytest.approx(2.0 * v1, rel=1e-12)

    def test_standard_errors(self):
        var = 0.05
        assert parametric_var_estimation_risk.var_se_equally_weighted(var, 100) == pytest.approx(
            var / math.sqrt(200), rel=1e-12
        )
        assert parametric_var_estimation_risk.var_se_ewma(var, 0.94) == pytest.approx(
            var * math.sqrt(0.06 / (2 * 1.94)), rel=1e-12
        )


class TestEwma:
    def test_recursion_matches_manual(self):
        returns = np.array([0.01, -0.02, 0.005, 0.03, -0.01])
        lam = 0.94
        # Independent hand recursion (mirrors Equation IV.2.79).
        expected = [float(np.var(returns))]
        for t in range(1, len(returns)):
            expected.append((1 - lam) * returns[t - 1] ** 2 + lam * expected[-1])
        got = ewma_variance_volatility.calculate_ewma_variance(returns, lam)
        np.testing.assert_allclose(got, expected, rtol=1e-12)

    def test_initial_variance_override(self):
        returns = np.array([0.01, -0.02, 0.005])
        got = ewma_variance_volatility.calculate_ewma_variance(returns, 0.94, initial_variance=0.5)
        assert got[0] == pytest.approx(0.5)
        assert got[1] == pytest.approx(0.06 * 0.01**2 + 0.94 * 0.5, rel=1e-12)

    def test_lambda_one_is_constant_variance(self):
        # lambda -> 1 puts all weight on the previous variance, so the series
        # stays at the initial (unconditional sample) variance.
        returns = np.array([0.01, -0.02, 0.005, 0.03])
        got = ewma_variance_volatility.calculate_ewma_variance(returns, 0.999999)
        np.testing.assert_allclose(got, np.var(returns), rtol=1e-4)

    def test_compute_facade(self):
        out = ewma_variance_volatility.compute(np.array([0.01, -0.02, 0.005]), 0.94, 250)
        assert out["model"] == "ewma"
        assert out["current_variance"] > 0.0
        assert out["annualized_volatility"] == pytest.approx(
            out["current_volatility"] * math.sqrt(250), rel=1e-12
        )


class TestGarch:
    def test_normal_loglik_hand(self):
        # Hand-computed GARCH(1,1) Gaussian log-likelihood on 3 points.
        returns = np.array([0.01, -0.02, 0.005])
        omega, alpha, beta = 0.0001, 0.1, 0.8
        s2 = [float(np.var(returns))]
        ll = 0.0
        for t in range(1, 3):
            s2.append(omega + alpha * returns[t - 1] ** 2 + beta * s2[-1])
            ll += (
                -0.5 * math.log(2 * math.pi)
                - 0.5 * math.log(s2[-1])
                - 0.5 * returns[t] ** 2 / s2[-1]
            )
        got = student_t_garch.normal_garch_loglik([omega, alpha, beta], returns)
        assert got == pytest.approx(-ll, rel=1e-10)

    def test_loglik_rejects_infeasible_params(self):
        returns = np.array([0.01, -0.02, 0.005])
        assert student_t_garch.normal_garch_loglik([-1.0, 0.1, 0.8], returns) == np.inf
        assert student_t_garch.normal_garch_loglik([1e-5, 0.6, 0.6], returns) == np.inf
        assert student_t_garch.student_t_garch_loglik([1e-5, 0.1, 0.8, 1.5], returns) == np.inf

    def test_conditional_variance_recursion(self):
        returns = np.array([0.01, -0.02, 0.005, 0.03, -0.01])
        omega, alpha, beta = 0.0001, 0.1, 0.8
        expected = [float(np.var(returns))]
        for t in range(1, len(returns)):
            expected.append(omega + alpha * returns[t - 1] ** 2 + beta * expected[-1])
        got = student_t_garch.garch11_conditional_variance(returns, omega, alpha, beta)
        np.testing.assert_allclose(got, expected, rtol=1e-12)

    @staticmethod
    def _snapshot_returns():
        # Deterministic GARCH(1,1) simulation used by the snapshot and the
        # `arch` cross-check: omega=2e-6, alpha=0.08, beta=0.90, T=2000,
        # standard normal innovations, numpy default_rng(20240607).
        rng = np.random.default_rng(20240607)
        T, w, a, b = 2000, 2e-6, 0.08, 0.90
        r = np.zeros(T)
        s2 = np.zeros(T)
        s2[0] = w / (1 - a - b)
        eps = rng.standard_normal(T)
        for t in range(1, T):
            s2[t] = w + a * r[t - 1] ** 2 + b * s2[t - 1]
            r[t] = np.sqrt(s2[t]) * eps[t]
        return r

    def test_estimate_pinned_snapshot(self):
        # Pinned reference snapshot (generated once with this implementation,
        # numpy 2.2 / scipy 1.15, Python 3.12, and reviewed against `arch`
        # 9.0 which agrees to ~0.2% on the conditional volatility). Tolerance
        # guards against optimizer-level platform jitter only.
        out = student_t_garch.compute(self._snapshot_returns(), dist="normal")
        assert out["converged"]
        assert out["alpha"] == pytest.approx(0.0748995074, abs=5e-3)
        assert out["beta"] == pytest.approx(0.9074879557, abs=5e-3)
        assert out["current_volatility"] == pytest.approx(0.0157426737, rel=2e-2)
        assert out["log_likelihood"] == pytest.approx(6569.3052323729, rel=1e-4)

    def test_estimate_recovers_true_persistence(self):
        out = student_t_garch.compute(self._snapshot_returns(), dist="normal")
        # True persistence alpha+beta = 0.98 for the simulated process.
        assert out["persistence"] == pytest.approx(0.98, abs=0.05)

    def test_estimate_vs_arch_package(self):
        arch = pytest.importorskip("arch")
        returns = self._snapshot_returns()
        ours = student_t_garch.compute(returns, dist="normal")
        fitted = arch.arch_model(
            returns * 100, mean="Zero", vol="GARCH", p=1, q=1, dist="normal"
        ).fit(disp="off")
        # Both maximize the same likelihood (different variance
        # initialization), so parameters agree only up to estimation noise.
        assert ours["alpha"] == pytest.approx(fitted.params["alpha[1]"], abs=0.03)
        assert ours["beta"] == pytest.approx(fitted.params["beta[1]"], abs=0.05)
        arch_last_vol = fitted.conditional_volatility[-1] / 100.0
        assert ours["current_volatility"] == pytest.approx(arch_last_vol, rel=0.05)


class TestRapms:
    def test_sharpe_closed_form(self):
        # (0.10 - 0.04) / 0.15 = 0.4 exactly.
        assert classical_rapms.calculate_sharpe_ratio(0.10, 0.04, 0.15) == pytest.approx(0.4)

    def test_sharpe_from_series(self):
        # mean = 0.004, std(ddof=1) = 0.01140175425099138 (hand via
        # deviations [-0.014, -0.024, 0.006, 0.026, -0.014]... see below).
        returns = np.array([-0.01, -0.02, 0.01, 0.03, -0.01])
        mean = float(np.mean(returns))
        std = float(np.std(returns, ddof=1))
        out = classical_rapms.compute(returns, risk_free_rate=0.001, periods_per_year=252)
        assert out["sharpe"] == pytest.approx((mean - 0.001) / std, rel=1e-12)
        assert out["sharpe_annualized"] == pytest.approx(out["sharpe"] * math.sqrt(252), rel=1e-12)

    def test_sortino_hand_case(self):
        # returns = [-0.02, 0.01, -0.03, 0.02, 0.04], rf = 0:
        # LPM2 = (0.02^2 + 0.03^2)/5 = 0.00026; mean = 0.004;
        # Sortino = 0.004/sqrt(0.00026) = 0.2480694691784169 (hand).
        returns = np.array([-0.02, 0.01, -0.03, 0.02, 0.04])
        got = downside_rapms.sortino_ratio(returns, 0.0)
        assert got == pytest.approx(0.2480694691784169, rel=1e-9)
        out = downside_rapms.compute(returns, risk_free_rate=0.0)
        assert out["lpm2"] == pytest.approx(0.00026, rel=1e-9)
        assert out["sortino"] == pytest.approx(0.2480694691784169, rel=1e-9)

    def test_kappa_degenerates_without_downside(self):
        # No returns below the threshold -> LPM = 0 -> +inf Kappa when the
        # mean exceeds the threshold.
        returns = np.array([0.01, 0.02, 0.03])
        assert downside_rapms.kappa_index(returns, 0.0, 2.0) == np.inf


class TestPortfolioRisk:
    # Two-asset closed form: w = [0.6, 0.4], sigma1 = 0.2, sigma2 = 0.1,
    # rho = 0.3 -> cov12 = 0.006; portfolio variance
    # = 0.6^2*0.04 + 0.4^2*0.01 + 2*0.6*0.4*0.006 = 0.01888 (hand).
    W = np.array([0.6, 0.4])
    COV = np.array([[0.04, 0.006], [0.006, 0.01]])

    def test_diversified_var_closed_form(self):
        # VaR = z_0.99 * sqrt(0.01888) = 0.3196506950693302 (hand, positions
        # sum to 1 so this is a loss fraction).
        out = stand_alone_var.compute(self.W, self.COV, confidence=0.99)
        assert out["total_var"] == pytest.approx(0.3196506950693302, rel=1e-9)

    def test_undiversified_var_closed_form(self):
        # Sum of stand-alone VaRs: z*(0.6*0.2 + 0.4*0.1) = z*0.16.
        out = stand_alone_var.compute(self.W, self.COV, confidence=0.99)
        expected = norm.ppf(0.99) * 0.16
        assert out["undiversified_var"] == pytest.approx(expected, rel=1e-12)
        assert out["undiversified_var"] > out["total_var"]

    def test_delvar_euler_decomposition(self):
        # Marginal (component) VaRs sum to the diversified VaR (Euler).
        out = delvar_gradient_marginal.compute(self.W, self.COV, confidence=0.99)
        assert sum(out["component_var"]) == pytest.approx(0.3196506950693302, rel=1e-9)
        # Gradient hand check: z * (Cov w) / sqrt(w' Cov w).
        vol = math.sqrt(0.01888)
        expected_grad = norm.ppf(0.99) * (self.COV @ self.W) / vol
        np.testing.assert_allclose(out["gradient"], expected_grad, rtol=1e-12)
        # Incremental VaR of trade [0.1, -0.1] = z*(0.1*grad0 - 0.1*grad1)/z
        trade = np.array([0.1, -0.1])
        out_trade = delvar_gradient_marginal.compute(self.W, self.COV, 0.99, trade=trade)
        assert out_trade["incremental_var"] == pytest.approx(
            float(trade @ expected_grad), rel=1e-12
        )

    def test_total_var_aggregation(self):
        # sqrt(250000^2 + 75000^2) = 261007.66272276375 (hand).
        assert total_var_aggregation.calculate_total_var(250_000, 75_000) == pytest.approx(
            261007.66272276375, rel=1e-12
        )
        out = total_var_aggregation.compute(250_000, 75_000)
        assert out["total_var"] == pytest.approx(261007.66272276375, rel=1e-12)

    def test_single_factor_decomposition(self):
        # beta=1.2, sigma_m=0.15, sigma_e=0.10: systematic risk = 0.18,
        # total variance = 0.18^2 + 0.10^2 = 0.0424, total risk = 0.2059126...
        out = single_factor_risk_decomposition.compute(1.2, 0.15, 0.10)
        assert out["systematic_risk"] == pytest.approx(0.18)
        assert out["total_variance"] == pytest.approx(0.0424, rel=1e-12)
        assert out["total_risk"] == pytest.approx(math.sqrt(0.0424), rel=1e-12)


class TestBacktests:
    def test_kupiec_hand(self):
        # LR_uc = -2 * [ln(0.01^4 * 0.99^246) - ln((4/250)^4 (246/250)^246)]
        # = 0.7691383643858458 (hand via math.log below).
        n, x, alpha = 250, 4, 0.01
        p = x / n
        ll_null = x * math.log(alpha) + (n - x) * math.log(1 - alpha)
        ll_alt = x * math.log(p) + (n - x) * math.log(1 - p)
        expected = -2.0 * (ll_null - ll_alt)
        stat, p_value = var_coverage_tests.kupiec_unconditional_coverage(n, x, alpha)
        assert stat == pytest.approx(expected, rel=1e-12)
        assert stat == pytest.approx(0.7691383643858458, rel=1e-9)
        # Below the chi2(1) 99% critical value 6.635 -> do not reject.
        assert stat < 6.635
        assert 0.0 < p_value < 1.0

    def test_kupiec_rejection_region(self):
        # x = 10 exceedances in 250 days at alpha = 0.01 is a clear reject:
        # LR = 12.955491062356018 (hand) > 6.635.
        stat, p_value = var_coverage_tests.kupiec_unconditional_coverage(250, 10, 0.01)
        assert stat == pytest.approx(12.955491062356018, rel=1e-9)
        assert stat > 6.635
        assert p_value < 0.01

    def test_kupiec_zero_exceedances(self):
        # Edge case: LR = -2 * 250 * ln(0.99) = 5.025167926750726 (hand).
        stat, _ = var_coverage_tests.kupiec_unconditional_coverage(250, 0, 0.01)
        assert stat == pytest.approx(5.025167926750726, rel=1e-9)

    def test_christoffersen_hand(self):
        # Text example transitions (2000 obs): n00=1936, n01=31, n10=31,
        # n11=2 -> LR_ind = 2.426776111049378 (hand via math.log below).
        n00, n01, n10, n11 = 1936, 31, 31, 2
        n0, n1 = n00 + n10, n01 + n11
        pi = n1 / (n0 + n1)
        pi_01, pi_11 = n01 / (n00 + n01), n11 / (n10 + n11)
        ll_null = n1 * math.log(pi) + n0 * math.log(1 - pi)
        ll_alt = (
            n00 * math.log(1 - pi_01)
            + n01 * math.log(pi_01)
            + n10 * math.log(1 - pi_11)
            + n11 * math.log(pi_11)
        )
        expected = -2.0 * (ll_null - ll_alt)
        stat, _ = var_coverage_tests.christoffersen_independence(n00, n01, n10, n11)
        assert stat == pytest.approx(expected, rel=1e-12)
        assert stat == pytest.approx(2.426776111049378, rel=1e-9)

    def test_conditional_coverage_is_sum(self):
        out = var_coverage_tests.compute(
            2000, 33, 0.99, transitions={"n00": 1936, "n01": 31, "n10": 31, "n11": 2}
        )
        assert out["conditional_coverage_stat"] == pytest.approx(
            out["kupiec_stat"] + out["christoffersen_stat"], rel=1e-12
        )

    def test_basel_traffic_light_zones(self):
        # Basel 1996 Amendment zones for a 250-day 1% VaR backtest:
        # 0-4 Green (3.0), 5-9 Yellow (3.4..3.85), 10+ Red (4.0).
        assert basel_regulatory_backtest.compute(0)["zone"] == "Green"
        assert basel_regulatory_backtest.compute(4)["zone"] == "Green"
        assert basel_regulatory_backtest.compute(5)["capital_multiplier"] == 3.4
        assert basel_regulatory_backtest.compute(9)["capital_multiplier"] == 3.85
        assert basel_regulatory_backtest.compute(10)["zone"] == "Red"
        assert basel_regulatory_backtest.compute(250)["capital_multiplier"] == 4.0


class TestOls:
    def test_hand_case(self):
        # x = [0,1,2,3], y = [1,2,2,4]: x̄=1.5, ȳ=2.25, sxx=5, sxy=4.5 ->
        # beta = 0.9, alpha = 0.9; rss = 0.7, tss = 4.75,
        # r2 = 1 - 0.7/4.75 = 0.8526315789473684; sigma2 = 0.35;
        # se_beta = sqrt(0.07), se_alpha = sqrt(0.245) (all hand).
        out = ols_regression_estimation.compute([1, 2, 2, 4], [0, 1, 2, 3])
        assert out["alpha"] == pytest.approx(0.9, rel=1e-9)
        assert out["beta"] == pytest.approx(0.9, rel=1e-12)
        assert out["r_squared"] == pytest.approx(0.8526315789473684, rel=1e-12)
        assert out["residual_std_error"] == pytest.approx(math.sqrt(0.35), rel=1e-12)
        assert out["beta_std_error"] == pytest.approx(math.sqrt(0.07), rel=1e-12)
        assert out["alpha_std_error"] == pytest.approx(math.sqrt(0.245), rel=1e-12)

    def test_vs_statsmodels(self):
        sm = pytest.importorskip("statsmodels.api")
        rng = np.random.default_rng(11)
        x = rng.normal(0.0, 1.0, 200)
        y = 1.5 + 2.5 * x + rng.normal(0.0, 0.5, 200)
        out = ols_regression_estimation.compute(y, x)
        results = sm.OLS(y, sm.add_constant(x)).fit()
        assert out["alpha"] == pytest.approx(results.params[0], rel=1e-9)
        assert out["beta"] == pytest.approx(results.params[1], rel=1e-9)
        assert out["alpha_std_error"] == pytest.approx(results.bse[0], rel=1e-9)
        assert out["beta_std_error"] == pytest.approx(results.bse[1], rel=1e-9)
        assert out["r_squared"] == pytest.approx(results.rsquared, rel=1e-12)
        assert out["beta_t"] == pytest.approx(results.tvalues[1], rel=1e-9)
        assert out["beta_p"] == pytest.approx(results.pvalues[1], rel=1e-6)

    def test_custom_beta_hypothesis_test(self):
        # Textbook Table I.4.7: t = (1.2885 - 1)/0.0427 = 6.7566... -> reject.
        t_stat, p_value = ols_regression_estimation.custom_beta_hypothesis_test(
            1.2885, 0.0427, 1.0, 752
        )
        assert t_stat == pytest.approx(6.7566, abs=1e-3)
        assert p_value < 1e-8


class TestCopulas:
    def test_clayton_kendall_tau_closed_form(self):
        # Clayton tau = alpha/(alpha+2); alpha=2 -> 0.5 exactly (Nelsen 2006).
        assert archimedean_copulas.kendall_tau_clayton(2.0) == pytest.approx(0.5)
        out = archimedean_copulas.compute("clayton", 2.0)
        assert out["kendall_tau"] == pytest.approx(0.5)
        # lambda_L = 2^(-1/alpha) = 2^-0.5 (closed form).
        assert out["lambda_lower"] == pytest.approx(2**-0.5, rel=1e-12)
        assert out["lambda_upper"] == 0.0

    def test_gumbel_kendall_tau_closed_form(self):
        # Gumbel tau = 1 - 1/delta; delta=2 -> 0.5 exactly.
        assert archimedean_copulas.kendall_tau_gumbel(2.0) == pytest.approx(0.5)
        out = archimedean_copulas.compute("gumbel", 2.0)
        assert out["kendall_tau"] == pytest.approx(0.5)
        # lambda_U = 2 - 2^(1/delta) = 2 - sqrt(2) (closed form).
        assert out["lambda_upper"] == pytest.approx(2 - math.sqrt(2), rel=1e-12)

    def test_clayton_density_hand(self):
        # alpha=2, u1=u2=0.5: density = 3 * (4+4-1)^(-2.5) * 0.5^-3 * 0.5^-3
        # = 192 * 7^(-2.5) = 1.481003649342278 (hand).
        out = archimedean_copulas.compute("clayton", 2.0, u1=0.5, u2=0.5)
        assert out["density"] == pytest.approx(1.481003649342278, rel=1e-9)

    def test_kendall_inversion(self):
        # Elliptical copula: rho = sin(pi/2 * tau); tau=0.5 -> sin(pi/4).
        out = copula_rank_calibration.compute(0.5, "kendall")
        assert out["rho"] == pytest.approx(math.sin(math.pi / 4), rel=1e-12)
        # Spearman: rho = 2 sin(pi/6 * rho_s); rho_s=0.5 -> 2 sin(pi/12).
        out_s = copula_rank_calibration.compute(0.5, "spearman")
        assert out_s["rho"] == pytest.approx(2 * math.sin(math.pi / 12), rel=1e-12)


class TestMonteCarlo:
    def test_simulation_reproducible_and_moments(self):
        means = np.array([0.001, -0.002])
        cov = np.array([[0.0004, 0.0001], [0.0001, 0.0009]])
        out1 = correlated_monte_carlo.compute(means, cov, num_simulations=20_000, seed=7)
        out2 = correlated_monte_carlo.compute(means, cov, num_simulations=20_000, seed=7)
        assert out1["seed"] == 7
        sim = np.array(out1["simulated_returns"])
        assert sim.shape == (20_000, 2)
        # Same seed -> identical draws.
        np.testing.assert_array_equal(sim, np.array(out2["simulated_returns"]))
        # Sample moments within Monte Carlo tolerance of the inputs.
        np.testing.assert_allclose(sim.mean(axis=0), means, atol=5e-4)
        np.testing.assert_allclose(np.cov(sim, rowvar=False), cov, atol=5e-5)

    def test_mc_var_converges_to_parametric(self):
        # Seeded: with 50k simulations of a fitted normal, MC VaR is within
        # 5% of the closed-form parametric VaR (MC quantile s.e. ~0.7%).
        rng = np.random.default_rng(5)
        returns = rng.normal(0.0004, 0.013, 1000)
        mc = api.compute_var(
            returns, method="montecarlo", confidence=0.99, num_simulations=50_000, seed=123
        )
        param = api.compute_var(returns, method="parametric", confidence=0.99)
        assert mc["var"] == pytest.approx(param["var"], rel=0.05)
        # Deterministic under a fixed seed.
        mc2 = api.compute_var(
            returns, method="montecarlo", confidence=0.99, num_simulations=50_000, seed=123
        )
        assert mc2["var"] == mc["var"]

    def test_copula_mc_var_matches_numpy_percentile(self):
        rng = np.random.default_rng(9)
        sim = rng.normal(0.0, 0.02, size=(5_000, 2))
        weights = np.array([0.75, 0.25])
        out = copula_monte_carlo_var.compute(sim, weights, confidence=0.99)
        expected = -float(np.percentile(sim @ weights, 1.0))
        assert out["var"] == pytest.approx(expected, rel=1e-12)


class TestDispatchLayer:
    @pytest.fixture()
    def returns(self):
        rng = np.random.default_rng(21)
        return rng.normal(0.0005, 0.012, 500)

    def test_compute_var_delegates(self, returns):
        direct = historical_simulation_var.compute(returns, confidence=0.95)
        via_api = api.compute_var(returns, method="historical", confidence=0.95)
        assert via_api == direct

    def test_compute_var_unknown_method(self, returns):
        with pytest.raises(KeyError, match="historical"):
            api.compute_var(returns, method="not-a-method")

    def test_compute_es_methods(self, returns):
        hist = api.compute_es(returns, method="historical", confidence=0.95)
        param = api.compute_es(returns, method="parametric", confidence=0.95)
        mc = api.compute_es(returns, method="montecarlo", confidence=0.95, seed=7)
        assert hist["es"] >= hist["var"] >= 0.0
        assert param["es"] > param["var"] > 0.0
        assert mc["es"] >= mc["var"] >= 0.0

    def test_parametric_es_closed_form(self, returns):
        # Normal ES: sigma * phi(z)/alpha - mu (closed form).
        out = api.compute_es(returns, method="parametric", confidence=0.99)
        mu = float(np.mean(returns))
        sigma = float(np.std(returns, ddof=1))
        z = float(norm.ppf(0.99))
        expected = sigma * float(norm.pdf(z)) / 0.01 - mu
        assert out["es"] == pytest.approx(expected, rel=1e-12)

    def test_compute_volatility_models(self, returns):
        ewma = api.compute_volatility(returns, model="ewma")
        assert ewma["model"] == "ewma" and ewma["current_volatility"] > 0.0
        garch = api.compute_volatility(returns, model="garch")
        assert garch["model"] == "garch" and garch["current_volatility"] > 0.0
        with pytest.raises(KeyError, match="ewma"):
            api.compute_volatility(returns, model="not-a-model")
        with pytest.raises(KeyError, match="student_t"):
            api.compute_volatility(returns, model="garch", dist="cauchy")

    def test_compute_portfolio_risk(self):
        rng = np.random.default_rng(31)
        base = rng.normal(0.0, 0.01, 300)
        matrix = np.column_stack([base, rng.normal(0.0, 0.02, 300)])
        weights = np.array([0.6, 0.4])
        out = api.compute_portfolio_risk(matrix, weights, confidence=0.99)
        # Independent recomputation from the sample covariance.
        cov = np.cov(matrix, rowvar=False, ddof=1)
        expected = float(norm.ppf(0.99) * np.sqrt(weights @ cov @ weights))
        assert out["diversified_var"] == pytest.approx(expected, rel=1e-9)
        assert sum(out["component_var"]) == pytest.approx(out["diversified_var"], rel=1e-9)
        assert out["assets"] == ["asset_0", "asset_1"]
        # DataFrame input carries column names through.
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame(matrix, columns=["EQ", "BD"])
        out_df = api.compute_portfolio_risk(df, weights, confidence=0.99)
        assert out_df["assets"] == ["EQ", "BD"]
        assert out_df["diversified_var"] == pytest.approx(out["diversified_var"], rel=1e-12)

    def test_compute_var_backtest_count_and_indicators(self):
        by_count = api.compute_var_backtest(4, 250, 0.99)
        assert by_count["kupiec"]["stat"] == pytest.approx(0.7691383643858458, rel=1e-9)
        assert by_count["basel"]["zone"] == "Green"
        assert "christoffersen" not in by_count

        indicators = np.zeros(250, dtype=int)
        indicators[[10, 50, 90, 200]] = 1
        by_ind = api.compute_var_backtest(indicators, 250, 0.99)
        assert by_ind["n_exceedances"] == 4
        assert by_ind["kupiec"]["stat"] == pytest.approx(by_count["kupiec"]["stat"], rel=1e-12)
        assert by_ind["christoffersen"]["transitions"] == {
            "n00": 241,
            "n01": 4,
            "n10": 4,
            "n11": 0,
        }
        assert by_ind["conditional_coverage"]["stat"] == pytest.approx(
            by_ind["kupiec"]["stat"] + by_ind["christoffersen"]["stat"], rel=1e-12
        )

    def test_results_are_json_serializable(self, returns):
        import json

        payloads = [
            api.compute_var(returns, "historical"),
            api.compute_var(returns, "parametric"),
            api.compute_var(returns, "montecarlo", num_simulations=500),
            api.compute_es(returns, "historical"),
            api.compute_es(returns, "parametric"),
            api.compute_es(returns, "montecarlo", num_simulations=500),
            api.compute_volatility(returns, "ewma"),
            api.compute_volatility(returns, "garch"),
            api.compute_portfolio_risk(np.column_stack([returns, returns * 0.5]), [0.5, 0.5]),
            api.compute_var_backtest(4, 250, 0.99),
        ]
        for payload in payloads:
            json.dumps(payload)  # must not raise
