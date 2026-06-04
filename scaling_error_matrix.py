import numpy as np
import pandas as pd

def generate_scaling_error_matrix(horizons: list, exponents: list, base_exponent: float = 0.5):
    """
    Generates Table IV.3.4: Scaling 1-day VaR for different risk horizons 
    and scale exponents relative to the square-root-of-time rule.
    """
    df = pd.DataFrame(index=horizons, columns=exponents)
    df.index.name = "Horizon (days)"
    
    for h in horizons:
        # The base multiplier if we mistakenly assume normality (c=0.5)
        base_multiplier = h ** base_exponent
        
        for c in exponents:
            # The true multiplier based on the empirical power law
            true_multiplier = h ** c
            
            if c == base_exponent:
                df.loc[h, c] = f"{base_multiplier:.2f}x"
            else:
                # Calculate what percentage the true VaR is compared to the naive Square-Root VaR
                percentage_of_base = true_multiplier / base_multiplier
                df.loc[h, c] = f"{percentage_of_base:.1%}"
                
    return df

# Parameters from Table IV.3.4
risk_horizons = [2, 5, 10, 30, 100, 250]
scale_exponents = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

error_matrix = generate_scaling_error_matrix(risk_horizons, scale_exponents)

print("Table IV.3.4: Scaling 1-day VaR for different scale exponents")
print("-" * 90)
print(error_matrix.to_string())
print("-" * 90)