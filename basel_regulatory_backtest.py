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