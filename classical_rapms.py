def calculate_sharpe_ratio(expected_return, risk_free_rate, volatility):
    """
    Calculates the Sharpe Ratio.
    """
    return (expected_return - risk_free_rate) / volatility

def calculate_treynor_ratio(alpha, beta):
    """
    Calculates the Treynor Ratio (using alpha and beta from a CAPM regression).
    """
    return alpha / beta

def calculate_information_ratio(alpha, specific_risk):
    """
    Calculates the Information Ratio (Appraisal Ratio).
    """
    return alpha / specific_risk

if __name__ == "__main__":
    # Example data
    e_r, r_f, vol = 0.10, 0.04, 0.15
    alpha, beta, specific_risk = 0.02, 1.2, 0.05
    
    print("--- Classical RAPMs ---")
    print(f"Sharpe Ratio: {calculate_sharpe_ratio(e_r, r_f, vol):.4f}")
    print(f"Treynor Ratio: {calculate_treynor_ratio(alpha, beta):.4f}")
    print(f"Information Ratio: {calculate_information_ratio(alpha, specific_risk):.4f}")