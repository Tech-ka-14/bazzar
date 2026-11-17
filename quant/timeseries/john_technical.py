"""Technical analysis toolkit.

Implements John Murphy's trend, momentum, volatility-band, volume, gap,
reversal-day, candlestick and retracement indicators as pandas column
transforms over OHLCV data.
"""

from typing import Union

import numpy as np
import pandas as pd


class TechnicalAnalyzer:
    """
    A comprehensive Technical Analysis toolkit implementing John Murphy's
    'Technical Analysis of the Financial Markets'.
    Designed to be robust against real-world imperfect data (NaNs, zeros).
    """

    def __init__(self, data_source: Union[str, pd.DataFrame]):
        """
        Initialize with a CSV file path or a pandas DataFrame.
        Expects columns: 'Open', 'High', 'Low', 'Close', 'Volume'
        """
        if isinstance(data_source, str):
            self.data = pd.read_csv(data_source)
        else:
            self.data = data_source.copy()

        # Standardize column names to handle lowercase/uppercase input gracefully
        self.data.columns = [col.capitalize() for col in self.data.columns]

    # =========================================================================
    # 1. TREND INDICATORS
    # =========================================================================
    def add_sma(self, period: int = 50, column: str = "Close"):
        """Simple Moving Average"""
        self.data[f"SMA_{period}"] = self.data[column].rolling(window=period).mean()
        return self.data

    def add_ema(self, period: int = 20, column: str = "Close"):
        """Exponential Moving Average"""
        self.data[f"EMA_{period}"] = self.data[column].ewm(span=period, adjust=False).mean()
        return self.data

    # =========================================================================
    # 2. MOMENTUM OSCILLATORS
    # =========================================================================
    def add_rsi(self, period: int = 14, column: str = "Close"):
        """Relative Strength Index (Wilder's Smoothing)"""
        delta = self.data[column].diff()

        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)

        # Calculate Wilder's Smoothing (alpha = 1/period)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        self.data[f"RSI_{period}"] = 100 - (100 / (1 + rs))

        # Handle edge case where avg_loss is 0 (RSI = 100)
        self.data.loc[avg_loss == 0, f"RSI_{period}"] = 100
        return self.data

    def add_macd(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "Close",
    ):
        """Moving Average Convergence Divergence"""
        ema_fast = self.data[column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = self.data[column].ewm(span=slow_period, adjust=False).mean()

        self.data["MACD_Line"] = ema_fast - ema_slow
        self.data["MACD_Signal"] = self.data["MACD_Line"].ewm(
            span=signal_period, adjust=False
        ).mean()
        self.data["MACD_Hist"] = self.data["MACD_Line"] - self.data["MACD_Signal"]
        return self.data

    def add_stochastic(self, k_period: int = 14, d_period: int = 3):
        """Stochastic Oscillator (%K and %D)"""
        low_min = self.data["Low"].rolling(window=k_period).min()
        high_max = self.data["High"].rolling(window=k_period).max()

        self.data["Stoch_%K"] = 100 * (
            (self.data["Close"] - low_min) / (high_max - low_min).replace(0, np.nan)
        )
        self.data["Stoch_%D"] = self.data["Stoch_%K"].rolling(window=d_period).mean()
        return self.data

    def add_williams_r(self, period: int = 14):
        """Williams %R"""
        high_max = self.data["High"].rolling(window=period).max()
        low_min = self.data["Low"].rolling(window=period).min()

        # Williams %R is traditionally negative (from 0 to -100)
        self.data[f"Williams_%R_{period}"] = -100 * (
            (high_max - self.data["Close"]) / (high_max - low_min)
        )
        return self.data

    # =========================================================================
    # 3. VOLATILITY & BANDS
    # =========================================================================
    def add_bollinger_bands(self, period: int = 20, std_dev: float = 2.0, column: str = "Close"):
        """Bollinger Bands"""
        sma = self.data[column].rolling(window=period).mean()
        rolling_std = self.data[column].rolling(window=period).std()

        self.data[f"BB_Middle_{period}"] = sma
        self.data[f"BB_Upper_{period}"] = sma + (rolling_std * std_dev)
        self.data[f"BB_Lower_{period}"] = sma - (rolling_std * std_dev)
        return self.data

    # =========================================================================
    # 4. VOLUME INDICATORS
    # =========================================================================
    def add_obv(self):
        """On-Balance Volume (OBV)"""
        price_change = np.sign(self.data["Close"].diff())
        # Fill NaN with 0 for the first calculation
        price_change = price_change.fillna(0)

        obv = (price_change * self.data["Volume"]).cumsum()
        self.data["OBV"] = obv
        return self.data

    # =========================================================================
    # 5. CHART PATTERNS & REVERSAL SIGNALS
    # =========================================================================
    def detect_gaps(self):
        """Detects Breakaway, Runaway, or Exhaustion Gaps"""
        self.data["Gap_Up"] = self.data["Low"] > self.data["High"].shift(1)
        self.data["Gap_Down"] = self.data["High"] < self.data["Low"].shift(1)
        return self.data

    def detect_reversal_days(self):
        """
        Detects Top and Bottom Reversal Days.
        Top Reversal: New high set, but closes lower than previous close.
        Bottom Reversal: New low set, but closes higher than previous close.
        """
        prev_close = self.data["Close"].shift(1)
        prev_high = self.data["High"].shift(1)
        prev_low = self.data["Low"].shift(1)

        # Basic Reversals
        self.data["Top_Reversal"] = (self.data["High"] > prev_high) & (
            self.data["Close"] < prev_close
        )
        self.data["Bottom_Reversal"] = (self.data["Low"] < prev_low) & (
            self.data["Close"] > prev_close
        )

        # Outside Reversals (Key Reversals with engulfing range)
        self.data["Outside_Top_Reversal"] = self.data["Top_Reversal"] & (
            self.data["Low"] < prev_low
        )
        self.data["Outside_Bottom_Reversal"] = self.data["Bottom_Reversal"] & (
            self.data["High"] > prev_high
        )

        return self.data

    # =========================================================================
    # 6. JAPANESE CANDLESTICKS
    # =========================================================================
    def detect_candlesticks(self):
        """Identifies basic candlestick patterns."""
        open_price = self.data["Open"]
        close_price = self.data["Close"]
        high_price = self.data["High"]
        low_price = self.data["Low"]

        # Body and Shadows
        body = np.abs(close_price - open_price)
        range_hl = high_price - low_price

        # Avoid division by zero
        range_hl = range_hl.replace(0, 0.0001)

        # Doji: Open and Close are almost the same (body < 10% of total range)
        self.data["Candle_Doji"] = body <= (0.10 * range_hl)

        # Bullish Engulfing: Black body followed by White body that completely covers the previous
        prev_open = open_price.shift(1)
        prev_close = close_price.shift(1)
        _prev_body = np.abs(prev_close - prev_open)  # retained for reference

        self.data["Candle_Bullish_Engulfing"] = (
            (close_price > open_price)  # White current
            & (prev_close < prev_open)  # Black previous
            & (open_price < prev_close)  # Open below prev close
            & (close_price > prev_open)  # Close above prev open
        )

        # Bearish Engulfing: White body followed by Black body that completely covers it
        self.data["Candle_Bearish_Engulfing"] = (
            (close_price < open_price)  # Black current
            & (prev_close > prev_open)  # White previous
            & (open_price > prev_close)  # Open above prev close
            & (close_price < prev_open)  # Close below prev open
        )

        return self.data

    # =========================================================================
    # 7. RETRACEMENTS
    # =========================================================================
    def calculate_retracements(self, swing_low: float, swing_high: float):
        """
        Calculates Dow Theory (33%, 50%, 66%) and Fibonacci (38.2%, 61.8%) retracements.
        """
        diff = swing_high - swing_low
        levels = {
            "0.0% (High)": swing_high,
            "33.3% (Dow Min)": swing_high - (diff * 0.333),
            "38.2% (Fibonacci)": swing_high - (diff * 0.382),
            "50.0% (Dow/Fib)": swing_high - (diff * 0.500),
            "61.8% (Fibonacci)": swing_high - (diff * 0.618),
            "66.6% (Dow Max)": swing_high - (diff * 0.666),
            "100.0% (Low)": swing_low,
        }
        return levels

    # =========================================================================
    # 8. EXECUTION
    # =========================================================================
    def run_all_analysis(self):
        """
        Executes all technical indicators and pattern recognition logic.
        """
        self.add_sma(period=50)
        self.add_sma(period=200)
        self.add_ema(period=20)
        self.add_rsi(period=14)
        self.add_macd()
        self.add_stochastic()
        self.add_williams_r()
        self.add_bollinger_bands()
        self.add_obv()
        self.detect_gaps()
        self.detect_reversal_days()
        self.detect_candlesticks()

        return self.data


def compute(data) -> dict:
    """Standard facade: latest technical indicator readings as a JSON dict.

    Parameters:
    data: pandas DataFrame (or dict of equal-length column lists) with
    Open/High/Low/Close/Volume columns (case-insensitive). At least 200 rows
    are needed for every indicator (SMA_200) to be defined.

    Returns:
    dict: {"n_rows", "indicators"} where indicators maps each computed
    indicator column to its latest value; values that are still undefined
    (insufficient history) are None.
    """
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if len(data) < 2:
        raise ValueError("data must contain at least two rows")

    analyzer = TechnicalAnalyzer(data)
    enriched = analyzer.run_all_analysis()

    base_cols = {c.capitalize() for c in ("Open", "High", "Low", "Close", "Volume")}
    indicator_cols = [c for c in enriched.columns if c not in base_cols]

    def _json_value(value):
        if pd.isna(value):
            return None
        if isinstance(value, (bool, np.bool_)):
            return bool(value)
        return float(value)

    latest = enriched.iloc[-1]
    return {
        "n_rows": int(len(enriched)),
        "indicators": {col: _json_value(latest[col]) for col in indicator_cols},
    }


if __name__ == "__main__":
    # Sample Mock Data matching typical Yahoo Finance format
    mock_data = pd.DataFrame(
        {
            "Open": np.random.normal(100, 2, 250),
            "High": np.random.normal(102, 2, 250),
            "Low": np.random.normal(98, 2, 250),
            "Close": np.random.normal(101, 2, 250),
            "Volume": np.random.randint(1000000, 5000000, 250),
        }
    )

    # Ensure High is always the max and Low is the min for realism
    mock_data["High"] = mock_data[["Open", "High", "Close"]].max(axis=1) + 1
    mock_data["Low"] = mock_data[["Open", "Low", "Close"]].min(axis=1) - 1

    # Run Analysis
    analyzer = TechnicalAnalyzer(mock_data)
    final_df = analyzer.run_all_analysis()

    print("Columns in final DataFrame:")
    print(final_df.columns.tolist())
    print("\nLast 5 rows:")
    print(final_df.tail())
