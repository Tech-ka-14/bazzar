import numpy as np

def build_crr_parameters(sigma, r, dt):
    """Calculates Cox-Ross-Rubinstein tree parameters."""
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d)
    return u, d, p

def binomial_put_pricing(S0, K, T, r, sigma, steps, is_american=False):
    """
    Prices a Put option using a Binomial Lattice.
    """
    dt = T / steps
    u, d, p = build_crr_parameters(sigma, r, dt)
    discount_factor = np.exp(-r * dt)
    
    # 1. Initialize asset prices at maturity
    asset_prices = np.array([S0 * (u ** j) * (d ** (steps - j)) for j in range(steps + 1)])
    
    # 2. Initialize option values at maturity (Payoff = max(K - S, 0))
    option_values = np.maximum(K - asset_prices, 0)
    
    # 3. Work backward through the tree
    for i in range(steps - 1, -1, -1):
        # Calculate expected discounted values from the next step
        expected_values = discount_factor * (p * option_values[1:i+2] + (1 - p) * option_values[0:i+1])
        
        if is_american:
            # Update asset prices for the current time step i
            current_prices = np.array([S0 * (u ** j) * (d ** (i - j)) for j in range(i + 1)])
            intrinsic_values = np.maximum(K - current_prices, 0)
            # American option takes the max of early exercise or waiting
            option_values = np.maximum(intrinsic_values, expected_values)
        else:
            option_values = expected_values
            
    return option_values[0]

if __name__ == "__main__":
    # --- Example I.5.9: Pricing European vs American Put ---
    S_current = 100
    Strike = 99
    RiskFree = 0.04
    Maturity = 200 / 365.0  # 200 days
    Steps = 4
    
    # To match the u=1.1 in the text example, we back out implied volatility
    dt = Maturity / Steps
    sigma_implied = np.log(1.1) / np.sqrt(dt) 

    euro_price = binomial_put_pricing(S_current, Strike, Maturity, RiskFree, sigma_implied, Steps, is_american=False)
    amer_price = binomial_put_pricing(S_current, Strike, Maturity, RiskFree, sigma_implied, Steps, is_american=True)
    
    print(f"4-Step Binomial European Put Price: {euro_price:.3f}")
    print(f"4-Step Binomial American Put Price: {amer_price:.3f}")