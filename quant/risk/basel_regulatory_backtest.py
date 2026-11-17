"""Basel traffic-light backtest for 1% daily VaR over 250 days.

Classifies a VaR model into the Green/Yellow/Red zones of the 1996 Basel
Amendment based on the number of exceedances observed in 250 trading days
and maps each zone to the capital multiplier (k factor added to 3.0).
"""


def basel_traffic_light_test(n_exceedances: int) -> dict:
    """
    Evaluates a VaR model based on the 1996 Amendment to the Basel Accord.
    Assumes a 250-day backtest of a 1% daily VaR.
    """
    if n_exceedances <= 4:
        zone = "Green"
        multiplier = 3.0
    elif n_exceedances == 5:
        zone = "Yellow"
        multiplier = 3.4
    elif n_exceedances == 6:
        zone = "Yellow"
        multiplier = 3.5
    elif n_exceedances == 7:
        zone = "Yellow"
        multiplier = 3.65
    elif n_exceedances == 8:
        zone = "Yellow"
        multiplier = 3.75
    elif n_exceedances == 9:
        zone = "Yellow"
        multiplier = 3.85
    else:
        zone = "Red"
        multiplier = 4.0  # Or model is completely disallowed

    return {"Zone": zone, "Capital Multiplier": multiplier, "Exceedances": n_exceedances}


def compute(n_exceedances: int) -> dict:
    """Standard facade: Basel traffic-light classification as a JSON dict.

    Returns:
    dict: {"zone", "capital_multiplier", "exceedances"}.
    """
    raw = basel_traffic_light_test(int(n_exceedances))
    return {
        "zone": raw["Zone"],
        "capital_multiplier": float(raw["Capital Multiplier"]),
        "exceedances": int(raw["Exceedances"]),
    }
