"""CAPM equilibrium expected return and Jensen's alpha.

CAPM: E[R_i] = r_f + beta_i (E[R_m] - r_f). Jensen's alpha is the asset's
actual return minus its CAPM equilibrium return; a positive alpha indicates
outperformance relative to equilibrium.
"""


def calculate_capm_expected_return(risk_free_rate, market_expected_return, beta):
    """
    Calculates the equilibrium expected return of an asset using CAPM.
    """
    market_risk_premium = market_expected_return - risk_free_rate
    expected_return = risk_free_rate + (beta * market_risk_premium)
    return expected_return


def calculate_jensens_alpha(actual_return, risk_free_rate, market_return, beta):
    """
    Calculates the Alpha of an asset (excess return over CAPM equilibrium).
    """
    expected_equilibrium_return = calculate_capm_expected_return(
        risk_free_rate, market_return, beta
    )
    alpha = actual_return - expected_equilibrium_return
    return alpha


def compute(
    risk_free_rate: float, market_expected_return: float, beta: float, actual_return: float = None
) -> dict:
    """Standard facade: CAPM expected return and alpha as a JSON dict.

    Parameters:
    risk_free_rate (float): Risk-free rate (fraction).
    market_expected_return (float): Expected market return (fraction).
    beta (float): Asset's CAPM beta.
    actual_return (float, optional): Realized asset return; when supplied,
    Jensen's alpha is included in the result.

    Returns:
    dict: {"beta", "capm_expected_return", "jensens_alpha"}; jensens_alpha
    is None when actual_return is not supplied.
    """
    capm_return = calculate_capm_expected_return(
        float(risk_free_rate), float(market_expected_return), float(beta)
    )
    alpha = None
    if actual_return is not None:
        alpha = float(
            calculate_jensens_alpha(
                float(actual_return),
                float(risk_free_rate),
                float(market_expected_return),
                float(beta),
            )
        )
    return {
        "beta": float(beta),
        "capm_expected_return": float(capm_return),
        "jensens_alpha": alpha,
    }


if __name__ == "__main__":
    r_f = 0.04
    r_m = 0.09
    asset_beta = 1.2

    # CAPM Expected Return
    capm_return = calculate_capm_expected_return(r_f, r_m, asset_beta)

    # Suppose the asset actually returned 12%
    actual_r = 0.12
    alpha = calculate_jensens_alpha(actual_r, r_f, r_m, asset_beta)

    print("--- CAPM and Alpha ---")
    print(f"CAPM Equilibrium Return: {capm_return * 100:.2f}%")
    print(f"Asset Alpha: {alpha * 100:.2f}% (Positive means underpriced/outperforming)")
