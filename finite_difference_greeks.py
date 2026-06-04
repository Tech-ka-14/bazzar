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
    gamma = (P_up - 2 * P_base + P_down) / (h_S ** 2)
    
    # Vega parameters (Volatility shifts)
    P_vol_up = pricing_func(S, sigma + h_sigma, **kwargs)
    P_vol_down = pricing_func(S, sigma - h_sigma, **kwargs)
    
    vega = (P_vol_up - P_vol_down) / (2 * h_sigma)
    
    return delta, gamma, vega