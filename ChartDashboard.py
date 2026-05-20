import pandas as pd
import numpy as np
import scipy.stats as si
import numpy_financial as npf

class FundamentalAnalyzer:
    """
    Production-grade Financial Analyzer.
    Processes OHLCV and fundamental data using vectorized operations.
    """
    
    def __init__(self, data_path: str):
        self.df = pd.read_csv(data_path)
        self.df.columns = [col.strip().lower() for col in self.df.columns]
        
    def calculate_ratios(self) -> pd.DataFrame:
        """Calculates core financial ratios safely across the dataframe."""
        df = self.df.copy()
        
        # Safe Division to prevent Infinity/ZeroDivision crashes
        df['current_ratio'] = np.where(
            df['current_liabilities'] == 0, 0, 
            df['current_assets'] / df['current_liabilities']
        )
        
        df['return_on_equity'] = np.where(
            df['total_equity'] == 0, 0,
            df['net_income'] / df['total_equity']
        )
        
        df['pe_ratio'] = np.where(
            df['eps'] <= 0, 0,  # Handle negative or zero earnings
            df['close'] / df['eps']
        )
        
        return df

    @staticmethod
    def calculate_wacc(equity: float, debt: float, cost_of_equity: float, cost_of_debt: float, tax_rate: float) -> float:
        """Calculates Weighted Average Cost of Capital (WACC)."""
        total_value = equity + debt
        if total_value == 0:
            return 0.0
            
        weight_equity = equity / total_value
        weight_debt = debt / total_value
        
        wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))
        return wacc

    @staticmethod
    def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculates European Call Option price using Black-Scholes Model.
        S: Spot Price, K: Strike, T: Time to maturity (years), r: Risk-free rate, sigma: Volatility.
        """
        if T <= 0 or sigma <= 0:
            return max(0.0, S - K)
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        call_price = (S * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0))
        return call_price

    def generate_technical_indicators(self, window: int = 14) -> pd.DataFrame:
        """Calculates technical indicators like SMA and RSI for the dashboard."""
        df = self.df.copy()
        df = df.sort_values(by=['ticker', 'date'])
        
        # Simple Moving Average
        df['sma_14'] = df.groupby('ticker')['close'].transform(lambda x: x.rolling(window=window).mean())
        
        # RSI Calculation (Vectorized)
        delta = df.groupby('ticker')['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.groupby(df['ticker']).rolling(window=window, min_periods=1).mean().reset_index(0, drop=True)
        avg_loss = loss.groupby(df['ticker']).rolling(window=window, min_periods=1).mean().reset_index(0, drop=True)
        
        rs = np.where(avg_loss == 0, 0, avg_gain / avg_loss)
        df['rsi'] = np.where(avg_loss == 0, 100, 100 - (100 / (1 + rs)))
        
        return df