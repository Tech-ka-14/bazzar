import math

def calculate_binomial_coefficient(N, m):
    """Calculates the binomial coefficient: N! / (m! * (N-m)!)"""
    return math.factorial(N) // (math.factorial(m) * math.factorial(N - m))

def binomial_asset_evolution(S0, u, d, p, days):
    """
    Calculates the terminal stock prices, their probabilities, and the 
    expected terminal price after a given number of days.
    
    :param S0: Initial stock price
    :param u: Multiplicative up factor
    :param d: Multiplicative down factor
    :param p: Probability of an up move
    :param days: Number of steps (N)
    """
    expected_price = 0
    results = []
    
    # Iterate through all possible number of 'up' moves (m from 0 to N)
    for m in range(days, -1, -1):
        down_moves = days - m
        
        # 1. Calculate terminal price for this path
        terminal_price = S0 * (u ** m) * (d ** down_moves)
        
        # 2. Calculate the number of paths leading to this price
        paths = calculate_binomial_coefficient(days, m)
        
        # 3. Calculate probability of this exact outcome
        probability = paths * (p ** m) * ((1 - p) ** down_moves)
        
        # 4. Add to expected value
        expected_price += terminal_price * probability
        
        results.append({
            'Up_Moves': m,
            'Price': terminal_price,
            'Paths': paths,
            'Probability': probability
        })
        
    return results, expected_price

# --- Testing with Example I.3.4 from the text ---
if __name__ == "__main__":
    S0 = 50.0       # Current price in pence
    u = 1.25        # Up factor
    d = 0.8         # Down factor
    p = 0.7         # Probability of up move
    days = 4        # 4 days from now
    
    outcomes, expected_S = binomial_asset_evolution(S0, u, d, p, days)
    
    print("--- Binomial Tree Outcomes (4 Days) ---")
    for outcome in outcomes:
        print(f"Price: {outcome['Price']:>7.3f} | Paths: {outcome['Paths']} | Prob: {outcome['Probability']:.4f}")
        
    print(f"\nExpected Stock Price in {days} days: {expected_S:.2f}")