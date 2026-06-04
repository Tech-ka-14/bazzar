def calculate_sharpe_ratio(expected_return, risk_free_rate, volatility):
    """
    Calculates the Sharpe ratio for a portfolio.
    """
    return (expected_return - risk_free_rate) / volatility

def capital_market_line(risk_free_rate, sharpe_ratio, target_volatility):
    """
    Calculates the expected return of a portfolio on the Capital Market Line (CML)
    given a target level of risk (volatility).
    """
    return risk_free_rate + (sharpe_ratio * target_volatility)

if __name__ == "__main__":
    # --- Example I.6.10 Implementation ---
    r_m = 0.10     # Market expected return = 10%
    sigma_m = 0.20 # Market standard deviation = 20%
    r_f = 0.05     # Risk-free rate = 5%
    
    # 1. Calculate the slope of the CML (Sharpe Ratio)
    market_sharpe = calculate_sharpe_ratio(r_m, r_f, sigma_m)
    
    # 2. Calculate the expected return for a portfolio with 15% volatility
    target_vol = 0.15
    portfolio_return = capital_market_line(r_f, market_sharpe, target_vol)
    
    print("--- Capital Market Line (CML) ---")
    print(f"CML Slope (Market Sharpe Ratio): {market_sharpe:.2f}")
    print(f"Expected Return for {target_vol*100}% volatility: {portfolio_return * 100:.2f}%")