import numpy as np

def calculate_active_risk_metrics(fund_returns, benchmark_returns):
    """
    Calculates Active Return, Raw Tracking Error, and Mean-Adjusted Tracking Error.
    
    Parameters:
    fund_returns (numpy.ndarray): 1D array of the fund's returns.
    benchmark_returns (numpy.ndarray): 1D array of the benchmark's returns.
    
    Returns:
    dict: A dictionary of calculated active risk metrics.
    """
    # Calculate the Active Returns series
    active_returns = fund_returns - benchmark_returns
    
    # 1. Expected Active Return (Mean Outperformance)
    mean_active_return = np.mean(active_returns)
    
    # 2. Raw Tracking Error (Root Mean Square around Zero)
    # Used primarily for passive index-tracking funds
    raw_tracking_error = np.sqrt(np.mean(active_returns ** 2))
    
    # 3. Mean-Adjusted Tracking Error (Sample Standard Deviation)
    # Used for active funds measuring volatility around the expected outperformance
    mean_adj_tracking_error = np.std(active_returns, ddof=1)
    
    return {
        "mean_active_return": float(mean_active_return),
        "raw_tracking_error": float(raw_tracking_error),
        "mean_adjusted_tracking_error": float(mean_adj_tracking_error)
    }

if __name__ == "__main__":
    # --- Example Application ---
    np.random.seed(42)
    T = 250 # Daily returns for a year
    
    benchmark = np.random.normal(0.0003, 0.015, T)
    
    # Simulate an active fund that consistently outperforms by 2 basis points a day, 
    # but introduces some idiosyncratic active risk (volatility)
    fund = benchmark + 0.0002 + np.random.normal(0, 0.005, T)
    
    metrics = calculate_active_risk_metrics(fund, benchmark)
    
    print("--- Active Risk and Tracking Error ---")
    print(f"Mean Active Return (Daily):   {metrics['mean_active_return'] * 10000:.2f} bps")
    print(f"Raw Tracking Error:           {metrics['raw_tracking_error'] * 100:.4f}%")
    print(f"Mean-Adjusted Tracking Error: {metrics['mean_adjusted_tracking_error'] * 100:.4f}%")
    print("\nNote: The text highlights that mean-adjusted tracking error is flawed as an absolute metric because it symmetricially penalizes upside outperformance.")