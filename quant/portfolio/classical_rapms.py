"""Classical risk-adjusted performance measures.

Sharpe ratio = (E[R] - r_f) / sigma; Treynor ratio = alpha / beta;
Information (appraisal) ratio = alpha / specific risk.
"""

import numpy as np


def calculate_sharpe_ratio(expected_return, risk_free_rate, volatility):
    """
    Calculates the Sharpe Ratio.
    """
    return (expected_return - risk_free_rate) / volatility


def calculate_treynor_ratio(alpha, beta):
    """
    Calculates the Treynor Ratio (using alpha and beta from a CAPM regression).
    """
    return alpha / beta


def calculate_information_ratio(alpha, specific_risk):
    """
    Calculates the Information Ratio (Appraisal Ratio).
    """
    return alpha / specific_risk


def compute(returns, risk_free_rate: float = 0.0, periods_per_year: int = 1) -> dict:
    """Standard facade: Sharpe ratio from a return series as a JSON dict.

    The periodic Sharpe ratio is (mean - r_f) / std(ddof=1); the annualized
    value scales it by sqrt(periods_per_year).

    Parameters:
    returns: 1-D array-like of periodic returns (fractions).
    risk_free_rate (float): Per-period risk-free rate.
    periods_per_year (int): Number of return periods in a year (1 = no
    annualization).

    Returns:
    dict: {"n", "risk_free_rate", "periods_per_year", "mean_return",
    "volatility", "sharpe", "sharpe_annualized"} with plain floats.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size < 2:
        raise ValueError("returns must contain at least two observations")

    mean_return = float(np.mean(returns))
    volatility = float(np.std(returns, ddof=1))
    if volatility == 0.0:
        raise ValueError("returns have zero volatility; Sharpe ratio is undefined")

    sharpe = calculate_sharpe_ratio(mean_return, float(risk_free_rate), volatility)
    return {
        "n": int(returns.size),
        "risk_free_rate": float(risk_free_rate),
        "periods_per_year": int(periods_per_year),
        "mean_return": mean_return,
        "volatility": volatility,
        "sharpe": float(sharpe),
        "sharpe_annualized": float(sharpe * np.sqrt(int(periods_per_year))),
    }


if __name__ == "__main__":
    # Example data
    e_r, r_f, vol = 0.10, 0.04, 0.15
    alpha, beta, specific_risk = 0.02, 1.2, 0.05

    print("--- Classical RAPMs ---")
    print(f"Sharpe Ratio: {calculate_sharpe_ratio(e_r, r_f, vol):.4f}")
    print(f"Treynor Ratio: {calculate_treynor_ratio(alpha, beta):.4f}")
    print(f"Information Ratio: {calculate_information_ratio(alpha, specific_risk):.4f}")
