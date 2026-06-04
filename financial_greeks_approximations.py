def delta_gamma_approximation(delta, gamma, delta_S):
    """
    Approximates the change in an option's price (PnL) using the first and 
    second partial derivatives with respect to the underlying asset's price.
    
    :param delta: First derivative (sensitivity to underlying price)
    :param gamma: Second derivative (convexity of price sensitivity)
    :param delta_S: Change in the underlying asset's price
    """
    linear_term = delta * delta_S
    quadratic_term = 0.5 * gamma * (delta_S ** 2)
    
    approx_pnl = linear_term + quadratic_term
    return approx_pnl

def delta_gamma_vega_approximation(delta, gamma, vega, delta_S, delta_vol):
    """
    Approximates the change in an option's price (PnL) using a multivariate 
    Taylor expansion, incorporating volatility.
    
    :param delta: First derivative w.r.t underlying price
    :param gamma: Second derivative w.r.t underlying price
    :param vega: First derivative w.r.t volatility
    :param delta_S: Change in the underlying asset's price
    :param delta_vol: Change in the underlying asset's volatility (absolute change)
    """
    price_effect = delta_gamma_approximation(delta, gamma, delta_S)
    volatility_effect = vega * delta_vol
    
    # Assuming cross-derivatives (e.g., vanna) are ignored as per the text
    approx_pnl = price_effect + volatility_effect
    return approx_pnl

# --- Testing the financial concepts ---
if __name__ == "__main__":
    # Concept check from the text:
    # Option A: delta = 0.5, gamma = 0.1
    # Option B: delta = 0.5, gamma = -0.1
    delta_val = 0.5
    gamma_A = 0.1
    gamma_B = -0.1
    
    # Scenario 1: Underlying price increases by €1
    inc_S = 1.0
    pnl_A_up = delta_gamma_approximation(delta_val, gamma_A, inc_S)
    pnl_B_up = delta_gamma_approximation(delta_val, gamma_B, inc_S)
    
    # Scenario 2: Underlying price decreases by €1
    dec_S = -1.0
    pnl_A_down = delta_gamma_approximation(delta_val, gamma_A, dec_S)
    pnl_B_down = delta_gamma_approximation(delta_val, gamma_B, dec_S)
    
    print("--- Delta-Gamma Approximation ---")
    print(f"Option A (Positive Gamma) -> +€1 move: +€{pnl_A_up:.2f} | -€1 move: €{pnl_A_down:.2f}")
    print(f"Option B (Negative Gamma) -> +€1 move: +€{pnl_B_up:.2f} | -€1 move: €{pnl_B_down:.2f}")
    
    # Multivariate check including Vega
    print("\n--- Delta-Gamma-Vega Approximation ---")
    vega_val = 0.2
    inc_vol = 0.05 # Implied volatility increases by 5%
    
    total_pnl = delta_gamma_vega_approximation(
        delta=delta_val, 
        gamma=gamma_A, 
        vega=vega_val, 
        delta_S=inc_S, 
        delta_vol=inc_vol
    )
    print(f"Option A with +5% Volatility Change -> Total PnL: +€{total_pnl:.3f}")