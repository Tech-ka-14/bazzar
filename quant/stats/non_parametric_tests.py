import numpy as np
import scipy.stats as stats


def perform_non_parametric_tests(sample1, sample2):
    """
    Performs Sign Test, Wilcoxon Signed-Rank, and Kolmogorov-Smirnov tests
    to compare two samples without assuming normality.
    """
    s1 = np.array(sample1)
    s2 = np.array(sample2)

    # 1. Sign Test (paired samples)
    differences = s1 - s2
    n_plus = np.sum(differences > 0)
    n_minus = np.sum(differences < 0)
    n_nonzero = n_plus + n_minus

    # Under H0, the number of positive signs follows a Binomial(n, 0.5)
    # Use the smaller of the two for a two-tailed test
    x_stat = min(n_plus, n_minus)
    sign_p_value = stats.binom.cdf(x_stat, n_nonzero, 0.5) * 2

    # 2. Wilcoxon Signed-Rank Test (paired samples)
    wilcoxon_stat, wilcoxon_p = stats.wilcoxon(s1, s2)

    # 3. Kolmogorov-Smirnov Test (independent samples)
    ks_stat, ks_p = stats.ks_2samp(s1, s2)

    return {
        "Sign Test": {"Positive Signs": n_plus, "Negative Signs": n_minus, "p-value": sign_p_value},
        "Wilcoxon Signed-Rank": {"Statistic": wilcoxon_stat, "p-value": wilcoxon_p},
        "Kolmogorov-Smirnov": {"Statistic": ks_stat, "p-value": ks_p},
    }


# --- Testing with Example I.3.17 from the text ---
if __name__ == "__main__":
    fund_A = [1.2, 2.1, -0.5, 1.8, 0.5, -1.2, 2.5, 1.0, -0.3, 1.5]
    fund_B = [0.8, 1.5, -1.0, 1.2, 0.2, -0.8, 2.0, 0.5, -0.5, 1.0]

    results = perform_non_parametric_tests(fund_A, fund_B)

    print("--- Non-Parametric Test Results ---")
    for test, values in results.items():
        print(f"{test}: {values}")
