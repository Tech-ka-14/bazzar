"""Simple OLS regression estimation.

Fits y = alpha + beta * x + epsilon by ordinary least squares and reports
the standard Excel-style output (R^2, residual standard error, ANOVA sums of
squares, coefficient standard errors and t-statistics). Reference: Alexander
(2008), Vol. I, Section I.4 (Tables I.4.5-I.4.7).
"""

import numpy as np
import scipy.stats as stats
import statsmodels.api as sm


def estimate_simple_linear_regression(y, x):
    """
    Fits an Ordinary Least Squares (OLS) regression model and
    extracts the key metrics matching standard Excel/statistical output.
    """
    # In statsmodels, you must explicitly add a constant to fit an intercept
    x_with_constant = sm.add_constant(x)

    # Fit the OLS model
    model = sm.OLS(y, x_with_constant)
    results = model.fit()

    # --- 1. Goodness of Fit (Table I.4.5 Equivalents) ---
    r_squared = results.rsquared
    adj_r_squared = results.rsquared_adj
    standard_error = np.sqrt(results.mse_resid)
    observations = int(results.nobs)

    print(f"R-Squared: {r_squared:.4f}")
    print(f"Adjusted R-Squared: {adj_r_squared:.4f}")
    print(f"Standard Error: {standard_error:.4f}")
    print(f"Observations: {observations}")
    print("-" * 30)

    # --- 2. ANOVA (Table I.4.6 Equivalents) ---
    ess = results.ess  # Explained Sum of Squares (Regression)
    rss = results.ssr  # Residual Sum of Squares
    tss = results.centered_tss  # Total Sum of Squares
    f_stat = results.fvalue

    print(f"Explained Sum of Squares (ESS): {ess:.4f}")
    print(f"Residual Sum of Squares (RSS): {rss:.4f}")
    print(f"Total Sum of Squares (TSS): {tss:.4f}")
    print(f"F-Statistic: {f_stat:.4f}")
    print("-" * 30)

    # --- 3. Coefficient Estimates (Table I.4.7 Equivalents) ---
    # results.params contains [intercept, slope]
    # results.bse contains standard errors
    # results.tvalues contains t-stats for H0: beta = 0
    # results.pvalues contains p-values

    print("Coefficients:")
    print(
        f"Intercept: {results.params[0]:.4f} (SE: {results.bse[0]:.4f}, t: {results.tvalues[0]:.4f}, p: {results.pvalues[0]:.4f})"
    )
    print(
        f"Slope (Beta): {results.params[1]:.4f} (SE: {results.bse[1]:.4f}, t: {results.tvalues[1]:.4f}, p: {results.pvalues[1]:.4f})"
    )

    return results


def custom_beta_hypothesis_test(beta_hat, standard_error, test_value=1.0, degrees_of_freedom=752):
    """
    Recreates the specific custom hypothesis test from the text:
    H0: beta = 1 vs H1: beta > 1
    """
    t_stat = (beta_hat - test_value) / standard_error

    # One-sided upper tail p-value
    p_value = 1 - stats.t.cdf(t_stat, df=degrees_of_freedom)

    return t_stat, p_value


def compute(y, x) -> dict:
    """Standard facade: simple OLS fit as a JSON-serializable dict.

    Fits y = alpha + beta * x by least squares (no printing, unlike
    ``estimate_simple_linear_regression``) and returns coefficient estimates
    with classical standard errors and two-sided p-values.

    Parameters:
    y, x: 1-D array-likes of equal length (at least 3 observations).

    Returns:
    dict: {"n", "alpha", "beta", "r_squared", "residual_std_error",
    "alpha_std_error", "beta_std_error", "alpha_t", "beta_t", "alpha_p",
    "beta_p"} with plain floats.
    """
    y = np.asarray(y, dtype=float).ravel()
    x = np.asarray(x, dtype=float).ravel()
    if y.shape != x.shape or y.size < 3:
        raise ValueError("y and x must have equal length of at least 3")
    if np.var(x) == 0.0:
        raise ValueError("x has zero variance; OLS slope is not identified")

    n = y.size
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    sxx = float(np.sum((x - x_mean) ** 2))
    sxy = float(np.sum((x - x_mean) * (y - y_mean)))
    beta = sxy / sxx
    alpha = y_mean - beta * x_mean

    residuals = y - (alpha + beta * x)
    rss = float(np.sum(residuals**2))
    tss = float(np.sum((y - y_mean) ** 2))
    r_squared = 1.0 - rss / tss if tss > 0.0 else 1.0

    dof = n - 2
    sigma2 = rss / dof
    beta_se = float(np.sqrt(sigma2 / sxx))
    alpha_se = float(np.sqrt(sigma2 * (1.0 / n + x_mean**2 / sxx)))

    beta_t = beta / beta_se
    alpha_t = alpha / alpha_se
    return {
        "n": int(n),
        "alpha": float(alpha),
        "beta": float(beta),
        "r_squared": float(r_squared),
        "residual_std_error": float(np.sqrt(sigma2)),
        "alpha_std_error": alpha_se,
        "beta_std_error": beta_se,
        "alpha_t": float(alpha_t),
        "beta_t": float(beta_t),
        "alpha_p": float(2.0 * stats.t.sf(abs(alpha_t), df=dof)),
        "beta_p": float(2.0 * stats.t.sf(abs(beta_t), df=dof)),
    }


if __name__ == "__main__":
    # --- Recreating the Custom Hypothesis Test from the Text ---
    print("\n--- Custom Hypothesis Test (H0: beta = 1 vs H1: beta > 1) ---")
    # Using the values directly from Table I.4.7
    estimated_beta = 1.2885
    se_beta = 0.0427
    df = 752  # 754 observations - 2 parameters

    t_statistic, p_val = custom_beta_hypothesis_test(
        estimated_beta, se_beta, test_value=1.0, degrees_of_freedom=df
    )
    print(f"Calculated t-statistic: {t_statistic:.4f}")  # Expected: ~6.756 (Text rounds to 6.76)
    print(f"P-value: {p_val:.6f}")
    print("Result: Reject H0. There is evidence to suggest the stock has a market beta > 1.")
