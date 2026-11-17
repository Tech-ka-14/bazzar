"""Finite-difference Greeks (Delta, Gamma, Vega).

Central differences of any pricing function f(S, sigma):
delta = [f(S+h) - f(S-h)] / 2h,
gamma = [f(S+h) - 2 f(S) + f(S-h)] / h^2,
vega = [f(sigma+h) - f(sigma-h)] / 2h.
"""


def calculate_finite_difference_greeks(pricing_func, S, sigma, h_S=1.0, h_sigma=0.0001, **kwargs):
    """
    Calculates Delta, Gamma, and Vega using central finite differences.

    Parameters:
    pricing_func (callable): Function returning the option price given (S, sigma).
    S (float): Current underlying price.
    sigma (float): Current implied volatility.
    h_S (float): Shift in underlying price.
    h_sigma (float): Shift in volatility.
    """
    # Base Price
    P_base = pricing_func(S, sigma, **kwargs)

    # Delta & Gamma parameters (Price shifts)
    P_up = pricing_func(S + h_S, sigma, **kwargs)
    P_down = pricing_func(S - h_S, sigma, **kwargs)

    delta = (P_up - P_down) / (2 * h_S)
    gamma = (P_up - 2 * P_base + P_down) / (h_S**2)

    # Vega parameters (Volatility shifts)
    P_vol_up = pricing_func(S, sigma + h_sigma, **kwargs)
    P_vol_down = pricing_func(S, sigma - h_sigma, **kwargs)

    vega = (P_vol_up - P_vol_down) / (2 * h_sigma)

    return delta, gamma, vega


def compute(
    pricing_func, S: float, sigma: float, h_S: float = 1.0, h_sigma: float = 0.0001, **kwargs
) -> dict:
    """Standard facade: finite-difference Greeks as a JSON dict.

    Parameters:
    pricing_func (callable): Pricing function f(S, sigma, **kwargs) — the
    primary input of this module, injected by the caller.
    S (float): Current underlying price.
    sigma (float): Current implied volatility.
    h_S (float): Shift in the underlying price, must be non-zero.
    h_sigma (float): Shift in volatility, must be non-zero.
    **kwargs: Extra keyword arguments forwarded to pricing_func.

    Returns:
    dict: {"s", "sigma", "h_S", "h_sigma", "delta", "gamma", "vega"} with
    plain floats.
    """
    if not callable(pricing_func):
        raise ValueError("pricing_func must be callable")
    if float(h_S) == 0.0 or float(h_sigma) == 0.0:
        raise ValueError("h_S and h_sigma must be non-zero")

    delta, gamma, vega = calculate_finite_difference_greeks(
        pricing_func, float(S), float(sigma), float(h_S), float(h_sigma), **kwargs
    )
    return {
        "s": float(S),
        "sigma": float(sigma),
        "h_S": float(h_S),
        "h_sigma": float(h_sigma),
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega),
    }
