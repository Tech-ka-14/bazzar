import numpy as np
import scipy.stats as stats


def z_test_population_mean(sample_data, mu0, sigma, alpha=0.05):
    """
    Performs a two-sided Z-test for a population mean when variance is KNOWN.
    """
    n = len(sample_data)
    x_bar = np.mean(sample_data)

    # Calculate the Z-statistic
    z_stat = (x_bar - mu0) / (sigma / np.sqrt(n))

    # Calculate critical value and p-value for a two-tailed test
    z_crit = stats.norm.ppf(1 - alpha / 2)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    reject_null = abs(z_stat) > z_crit

    print("--- Z-Test (Known Variance) ---")
    print(f"H0: mu = {mu0} | Sample Mean: {x_bar:.4f}")
    print(f"Z-statistic: {z_stat:.4f} | Critical Value: +/- {z_crit:.4f}")
    print(f"P-value: {p_value:.4f}")
    print(
        f"Conclusion: {'Reject H0' if reject_null else 'Fail to reject H0'} at {alpha * 100}% significance.\n"
    )


def t_test_population_mean(sample_data, mu0, alpha=0.05):
    """
    Performs a two-sided t-test for a population mean when variance is UNKNOWN.
    """
    n = len(sample_data)
    x_bar = np.mean(sample_data)
    s = np.std(sample_data, ddof=1)  # Sample standard deviation

    # Calculate the t-statistic
    t_stat = (x_bar - mu0) / (s / np.sqrt(n))

    # Degrees of freedom = n - 1
    df = n - 1

    # Calculate critical value and p-value for a two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    reject_null = abs(t_stat) > t_crit

    print("--- t-Test (Unknown Variance) ---")
    print(f"H0: mu = {mu0} | Sample Mean: {x_bar:.4f}")
    print(f"t-statistic: {t_stat:.4f} | Critical Value: +/- {t_crit:.4f} (df={df})")
    print(f"P-value: {p_value:.4f}")
    print(
        f"Conclusion: {'Reject H0' if reject_null else 'Fail to reject H0'} at {alpha * 100}% significance.\n"
    )


def chi_squared_test_variance(sample_data, sigma0_sq, alpha=0.05):
    """
    Performs a two-sided Chi-squared test for a population variance.
    """
    n = len(sample_data)
    s_sq = np.var(sample_data, ddof=1)

    # Calculate the Chi-squared statistic
    chi2_stat = ((n - 1) * s_sq) / sigma0_sq

    df = n - 1

    # Calculate critical values for a two-tailed test
    chi2_crit_lower = stats.chi2.ppf(alpha / 2, df)
    chi2_crit_upper = stats.chi2.ppf(1 - alpha / 2, df)

    # Calculate p-value
    p_value = 2 * min(
        stats.chi2.cdf(chi2_stat, df), 1 - stats.chi2.cdf(chi2_stat, df)
    )

    reject_null = (chi2_stat < chi2_crit_lower) or (chi2_stat > chi2_crit_upper)

    print("--- Chi-Squared Test (Variance) ---")
    print(f"H0: sigma^2 = {sigma0_sq} | Sample Variance: {s_sq:.4f}")
    print(f"Chi2-statistic: {chi2_stat:.4f} | df={df}")
    print(f"Critical Range: [{chi2_crit_lower:.4f}, {chi2_crit_upper:.4f}]")
    print(f"P-value: {p_value:.4f}")
    print(
        f"Conclusion: {'Reject H0' if reject_null else 'Fail to reject H0'} at {alpha * 100}% significance.\n"
    )


# --- Testing with hypothetical financial returns ---
if __name__ == "__main__":
    # Hypothetical sample of 20 daily returns
    np.random.seed(42)
    sample_returns = np.random.normal(0.001, 0.02, 20)

    # Test if mean return is significantly different from 0 (assuming true vol is 2%)
    z_test_population_mean(sample_returns, mu0=0, sigma=0.02, alpha=0.05)

    # Test if mean return is significantly different from 0 (unknown vol)
    t_test_population_mean(sample_returns, mu0=0, alpha=0.05)

    # Test if variance is significantly different from 0.0004 (2% daily vol squared)
    chi_squared_test_variance(sample_returns, sigma0_sq=0.0004, alpha=0.05)
