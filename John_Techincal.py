import pandas as pd
import numpy as np

class TechnicalAnalyzer:
    """
    A comprehensive engine for performing technical analysis on financial data,
    incorporating concepts from Trend Analysis, Momentum Oscillators, Volume 
    Analysis, and Japanese Candlesticks.
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initializes the analyzer with a pandas DataFrame.
        Expected columns: 'Open', 'High', 'Low', 'Close', 'Volume'
        """
        self.data = data.copy()
        # Ensure column names are standard
        self.data.rename(columns=lambda x: x.capitalize(), inplace=True)
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in self.data.columns:
                raise ValueError(f"Missing required column: {col}")

    # =========================================================================
    # 1. TREND INDICATORS (Moving Averages)
    # =========================================================================
    def add_sma(self, period: int, column: str = 'Close'):
        """Simple Moving Average (SMA)"""
        self.data[f'SMA_{period}'] = self.data[column].rolling(window=period).mean()
        return self.data

    def add_ema(self, period: int, column: str = 'Close'):
        """Exponential Moving Average (EMA)"""
        self.data[f'EMA_{period}'] = self.data[column].ewm(span=period, adjust=False).mean()
        return self.data

    def add_wma(self, period: int, column: str = 'Close'):
        """Linearly Weighted Moving Average (WMA)"""
        weights = np.arange(1, period + 1)
        self.data[f'WMA_{period}'] = self.data[column].rolling(window=period).apply(
            lambda prices: np.dot(prices, weights) / weights.sum(), raw=True
        )
        return self.data

    # =========================================================================
    # 2. OSCILLATORS & MOMENTUM
    # =========================================================================
    def add_rsi(self, period: int = 14, column: str = 'Close'):
        """Relative Strength Index (RSI)"""
        delta = self.data[column].diff(1)
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        self.data[f'RSI_{period}'] = 100 - (100 / (1 + rs))
        return self.data

    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9, column: str = 'Close'):
        """Moving Average Convergence Divergence (MACD)"""
        fast_ema = self.data[column].ewm(span=fast, adjust=False).mean()
        slow_ema = self.data[column].ewm(span=slow, adjust=False).mean()
        
        self.data['MACD_Line'] = fast_ema - slow_ema
        self.data['MACD_Signal'] = self.data['MACD_Line'].ewm(span=signal, adjust=False).mean()
        self.data['MACD_Histogram'] = self.data['MACD_Line'] - self.data['MACD_Signal']
        return self.data

    def add_stochastic(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3):
        """Stochastic Oscillator (%K and %D)"""
        low_min = self.data['Low'].rolling(window=period).min()
        high_max = self.data['High'].rolling(window=period).max()
        
        self.data['Stoch_%K_raw'] = 100 * ((self.data['Close'] - low_min) / (high_max - low_min))
        self.data['Stoch_%K'] = self.data['Stoch_%K_raw'].rolling(window=smooth_k).mean()
        self.data['Stoch_%D'] = self.data['Stoch_%K'].rolling(window=smooth_d).mean()
        self.data.drop(columns=['Stoch_%K_raw'], inplace=True)
        return self.data

    def add_williams_r(self, period: int = 14):
        """Williams %R"""
        high_max = self.data['High'].rolling(window=period).max()
        low_min = self.data['Low'].rolling(window=period).min()
        
        # Williams %R is traditionally negative (from 0 to -100)
        self.data[f'Williams_%R_{period}'] = -100 * ((high_max - self.data['Close']) / (high_max - low_min))
        return self.data

    # =========================================================================
    # 3. VOLATILITY & BANDS
    # =========================================================================
    def add_bollinger_bands(self, period: int = 20, std_dev: float = 2.0, column: str = 'Close'):
        """Bollinger Bands"""
        sma = self.data[column].rolling(window=period).mean()
        rolling_std = self.data[column].rolling(window=period).std()
        
        self.data[f'BB_Middle_{period}'] = sma
        self.data[f'BB_Upper_{period}'] = sma + (rolling_std * std_dev)
        self.data[f'BB_Lower_{period}'] = sma - (rolling_std * std_dev)
        return self.data

    # =========================================================================
    # 4. VOLUME INDICATORS
    # =========================================================================
    def add_obv(self):
        """On-Balance Volume (OBV)"""
        price_change = np.sign(self.data['Close'].diff())
        # Fill NaN with 0 for the first calculation
        price_change = price_change.fillna(0)
        
        obv = (price_change * self.data['Volume']).cumsum()
        self.data['OBV'] = obv
        return self.data

    # =========================================================================
    # 5. CHART PATTERNS & REVERSAL SIGNALS
    # =========================================================================
    def detect_gaps(self):
        """Detects Breakaway, Runaway, or Exhaustion Gaps"""
        self.data['Gap_Up'] = self.data['Low'] > self.data['High'].shift(1)
        self.data['Gap_Down'] = self.data['High'] < self.data['Low'].shift(1)
        return self.data

    def detect_reversal_days(self):
        """
        Detects Top and Bottom Reversal Days.
        Top Reversal: New high set, but closes lower than previous close.
        Bottom Reversal: New low set, but closes higher than previous close.
        """
        prev_close = self.data['Close'].shift(1)
        prev_high = self.data['High'].shift(1)
        prev_low = self.data['Low'].shift(1)

        # Basic Reversals
        self.data['Top_Reversal'] = (self.data['High'] > prev_high) & (self.data['Close'] < prev_close)
        self.data['Bottom_Reversal'] = (self.data['Low'] < prev_low) & (self.data['Close'] > prev_close)
        
        # Outside Reversals (Key Reversals with engulfing range)
        self.data['Outside_Top_Reversal'] = self.data['Top_Reversal'] & (self.data['Low'] < prev_low)
        self.data['Outside_Bottom_Reversal'] = self.data['Bottom_Reversal'] & (self.data['High'] > prev_high)
        
        return self.data

    # =========================================================================
    # 6. JAPANESE CANDLESTICKS
    # =========================================================================
    def detect_candlesticks(self):
        """Identifies basic candlestick patterns."""
        open_price = self.data['Open']
        close_price = self.data['Close']
        high_price = self.data['High']
        low_price = self.data['Low']

        # Body and Shadows
        body = np.abs(close_price - open_price)
        range_hl = high_price - low_price
        
        # Avoid division by zero
        range_hl = range_hl.replace(0, 0.0001)

        # Doji: Open and Close are almost the same (body < 10% of total range)
        self.data['Candle_Doji'] = body <= (0.10 * range_hl)

        # Bullish Engulfing: Black body followed by White body that completely covers the previous
        prev_open = open_price.shift(1)
        prev_close = close_price.shift(1)
        prev_body = np.abs(prev_close - prev_open)
        
        self.data['Candle_Bullish_Engulfing'] = (
            (close_price > open_price) &  # White current
            (prev_close < prev_open) &    # Black previous
            (open_price < prev_close) &   # Open below prev close
            (close_price > prev_open)     # Close above prev open
        )

        # Bearish Engulfing: White body followed by Black body that completely covers it
        self.data['Candle_Bearish_Engulfing'] = (
            (close_price < open_price) &  # Black current
            (prev_close > prev_open) &    # White previous
            (open_price > prev_close) &   # Open above prev close
            (close_price < prev_open)     # Close below prev open
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
            "100.0% (Low)": swing_low
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