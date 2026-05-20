# fundamental_analyzer.py

import pandas as pd
import numpy as np
import numpy_financial as npf
from scipy.stats import norm
import math
from typing import Union, List, Optional, Dict

class FundamentalAnalyzer:
    """
    A comprehensive Fundamental Analysis and Corporate Finance toolkit.
    Extracts formulas from corporate finance principles, heavily fortified 
    with production-grade error handling to prevent UI crashes when 
    processing imperfect CSV data.
    """

    def __init__(self, data_source: Union[str, pd.DataFrame, None] = None):
        """
        Initialize the analyzer with a dataset (CSV path or pandas DataFrame).
        """
        if isinstance(data_source, str):
            try:
                self.data = pd.read_csv(data_source)
            except Exception as e:
                print(f"Error loading CSV: {e}")
                self.data = pd.DataFrame()
        elif isinstance(data_source, pd.DataFrame):
            self.data = data_source
        else:
            self.data = pd.DataFrame()

    # ==========================================
    # HELPER METHODS
    # ==========================================
    @staticmethod
    def safe_div(numerator: float, denominator: float) -> float:
        """Safely divide two numbers, returning NaN if the denominator is zero or invalid."""
        if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
            return np.nan
        return float(numerator / denominator)

    # ==========================================
    # CHAPTER 2: FINANCIAL STATEMENTS & CASH FLOW
    # ==========================================
    @staticmethod
    def net_working_capital(current_assets: float, current_liabilities: float) -> float:
        return float(current_assets - current_liabilities)

    @staticmethod
    def operating_cash_flow(ebit: float, depreciation: float, taxes: float) -> float:
        return float(ebit + depreciation - taxes)

    @staticmethod
    def net_capital_spending(ending_nfa: float, beginning_nfa: float, depreciation: float) -> float:
        return float(ending_nfa - beginning_nfa + depreciation)

    @staticmethod
    def cash_flow_from_assets(ocf: float, net_capital_spending: float, change_in_nwc: float) -> float:
        """Also known as Free Cash Flow (FCF)"""
        return float(ocf - net_capital_spending - change_in_nwc)

    @staticmethod
    def cash_flow_to_creditors(interest_paid: float, net_new_borrowing: float) -> float:
        return float(interest_paid - net_new_borrowing)

    @staticmethod
    def cash_flow_to_stockholders(dividends_paid: float, net_new_equity_raised: float) -> float:
        return float(dividends_paid - net_new_equity_raised)

    # ==========================================
    # CHAPTER 3: FINANCIAL RATIOS & MODELS
    # ==========================================
    
    # --- Short-Term Solvency (Liquidity) Ratios ---
    @classmethod
    def current_ratio(cls, current_assets: float, current_liabilities: float) -> float:
        return cls.safe_div(current_assets, current_liabilities)

    @classmethod
    def quick_ratio(cls, current_assets: float, inventory: float, current_liabilities: float) -> float:
        return cls.safe_div(current_assets - inventory, current_liabilities)

    @classmethod
    def cash_ratio(cls, cash: float, current_liabilities: float) -> float:
        return cls.safe_div(cash, current_liabilities)

    # --- Long-Term Solvency (Leverage) Ratios ---
    @classmethod
    def total_debt_ratio(cls, total_assets: float, total_equity: float) -> float:
        return cls.safe_div(total_assets - total_equity, total_assets)

    @classmethod
    def debt_equity_ratio(cls, total_debt: float, total_equity: float) -> float:
        return cls.safe_div(total_debt, total_equity)

    @classmethod
    def equity_multiplier(cls, total_assets: float, total_equity: float) -> float:
        return cls.safe_div(total_assets, total_equity)

    @classmethod
    def times_interest_earned(cls, ebit: float, interest: float) -> float:
        return cls.safe_div(ebit, interest)

    @classmethod
    def cash_coverage_ratio(cls, ebitda: float, interest: float) -> float:
        return cls.safe_div(ebitda, interest)

    # --- Asset Management (Turnover) Ratios ---
    @classmethod
    def inventory_turnover(cls, cogs: float, inventory: float) -> float:
        return cls.safe_div(cogs, inventory)

    @classmethod
    def days_sales_in_inventory(cls, inventory_turnover: float) -> float:
        return cls.safe_div(365, inventory_turnover)

    @classmethod
    def receivables_turnover(cls, sales: float, accounts_receivable: float) -> float:
        return cls.safe_div(sales, accounts_receivable)

    @classmethod
    def days_sales_in_receivables(cls, receivables_turnover: float) -> float:
        return cls.safe_div(365, receivables_turnover)

    @classmethod
    def total_asset_turnover(cls, sales: float, total_assets: float) -> float:
        return cls.safe_div(sales, total_assets)
        
    @classmethod
    def capital_intensity(cls, total_assets: float, sales: float) -> float:
        return cls.safe_div(total_assets, sales)

    # --- Profitability Ratios ---
    @classmethod
    def profit_margin(cls, net_income: float, sales: float) -> float:
        return cls.safe_div(net_income, sales)

    @classmethod
    def return_on_assets(cls, net_income: float, total_assets: float) -> float:
        return cls.safe_div(net_income, total_assets)

    @classmethod
    def return_on_equity(cls, net_income: float, total_equity: float) -> float:
        return cls.safe_div(net_income, total_equity)

    @staticmethod
    def dupont_identity(profit_margin: float, total_asset_turnover: float, equity_multiplier: float) -> float:
        """ROE = Profit Margin * Total Asset Turnover * Equity Multiplier"""
        return float(profit_margin * total_asset_turnover * equity_multiplier)

    # --- Market Value Ratios ---
    @classmethod
    def earnings_per_share(cls, net_income: float, shares_outstanding: float) -> float:
        return cls.safe_div(net_income, shares_outstanding)

    @classmethod
    def price_earnings_ratio(cls, price_per_share: float, eps: float) -> float:
        return cls.safe_div(price_per_share, eps)

    @classmethod
    def market_to_book_ratio(cls, price_per_share: float, book_value_per_share: float) -> float:
        return cls.safe_div(price_per_share, book_value_per_share)

    @staticmethod
    def market_capitalization(price_per_share: float, shares_outstanding: float) -> float:
        return float(price_per_share * shares_outstanding)

    @staticmethod
    def enterprise_value(market_cap: float, market_value_interest_bearing_debt: float, cash: float) -> float:
        return float(market_cap + market_value_interest_bearing_debt - cash)

    @classmethod
    def enterprise_value_multiple(cls, enterprise_value: float, ebitda: float) -> float:
        return cls.safe_div(enterprise_value, ebitda)

    # --- Growth Rates ---
    @classmethod
    def internal_growth_rate(cls, roa: float, plowback_ratio: float) -> float:
        """Maximum growth rate achievable without external financing."""
        denominator = 1 - (roa * plowback_ratio)
        return cls.safe_div(roa * plowback_ratio, denominator)

    @classmethod
    def sustainable_growth_rate(cls, roe: float, plowback_ratio: float) -> float:
        """Maximum growth rate achievable without external equity financing while maintaining constant debt-equity ratio."""
        denominator = 1 - (roe * plowback_ratio)
        return cls.safe_div(roe * plowback_ratio, denominator)


    # ==========================================
    # CHAPTER 4: DISCOUNTED CASH FLOW VALUATION
    # ==========================================
    @staticmethod
    def effective_annual_rate(stated_annual_rate: float, compounding_periods: int) -> float:
        if compounding_periods <= 0:
            return np.nan
        return (1 + (stated_annual_rate / compounding_periods)) ** compounding_periods - 1

    @classmethod
    def present_value_perpetuity(cls, cash_flow: float, discount_rate: float) -> float:
        return cls.safe_div(cash_flow, discount_rate)

    @classmethod
    def present_value_growing_perpetuity(cls, cash_flow_period_1: float, discount_rate: float, growth_rate: float) -> float:
        if discount_rate <= growth_rate:
            return np.nan # Value is infinite if g >= r
        return cls.safe_div(cash_flow_period_1, (discount_rate - growth_rate))

    @classmethod
    def present_value_annuity(cls, cash_flow: float, discount_rate: float, periods: int) -> float:
        if discount_rate == 0:
            return float(cash_flow * periods)
        pv_factor = cls.safe_div(1 - (1 / ((1 + discount_rate) ** periods)), discount_rate)
        return cash_flow * pv_factor if not pd.isna(pv_factor) else np.nan

    @classmethod
    def present_value_growing_annuity(cls, cash_flow_1: float, discount_rate: float, growth_rate: float, periods: int) -> float:
        if discount_rate == growth_rate:
            return cash_flow_1 * periods / (1 + discount_rate)
        pv_factor = cls.safe_div(1 - ((1 + growth_rate) / (1 + discount_rate)) ** periods, discount_rate - growth_rate)
        return cash_flow_1 * pv_factor if not pd.isna(pv_factor) else np.nan

    # ==========================================
    # CHAPTER 5: BOND VALUATION
    # ==========================================
    @classmethod
    def bond_value(cls, face_value: float, coupon_rate: float, periods_to_maturity: int, yield_to_maturity: float, frequency: int = 1) -> float:
        if frequency <= 0 or periods_to_maturity < 0:
            return np.nan
        
        c = (coupon_rate * face_value) / frequency
        r = yield_to_maturity / frequency
        t = periods_to_maturity * frequency
        
        pv_coupons = cls.present_value_annuity(c, r, t)
        pv_face = face_value / ((1 + r) ** t)
        
        if pd.isna(pv_coupons):
            return np.nan
        return float(pv_coupons + pv_face)

    @staticmethod
    def fisher_effect_real_rate(nominal_rate: float, inflation_rate: float) -> float:
        """Exact Fisher effect relation: (1 + R) = (1 + r)(1 + h)"""
        return ((1 + nominal_rate) / (1 + inflation_rate)) - 1

    # ==========================================
    # CHAPTER 6: STOCK VALUATION (DDM)
    # ==========================================
    @classmethod
    def stock_value_zero_growth(cls, dividend: float, required_return: float) -> float:
        return cls.safe_div(dividend, required_return)

    @classmethod
    def stock_value_constant_growth(cls, current_dividend: float, growth_rate: float, required_return: float) -> float:
        if required_return <= growth_rate:
            return np.nan # Undefined/Infinite
        next_dividend = current_dividend * (1 + growth_rate)
        return cls.safe_div(next_dividend, (required_return - growth_rate))

    # ==========================================
    # CHAPTER 7 & 8: CAPITAL BUDGETING RULES
    # ==========================================
    @staticmethod
    def net_present_value(rate: float, cash_flows: List[float]) -> float:
        try:
            return float(npf.npv(rate, cash_flows))
        except Exception:
            return np.nan

    @staticmethod
    def internal_rate_of_return(cash_flows: List[float]) -> float:
        try:
            return float(npf.irr(cash_flows))
        except Exception:
            return np.nan

    @classmethod
    def profitability_index(cls, rate: float, cash_flows: List[float]) -> float:
        if not cash_flows or len(cash_flows) < 2:
            return np.nan
        initial_investment = abs(cash_flows[0])
        pv_future_cf = npf.npv(rate, [0] + cash_flows[1:])
        return cls.safe_div(pv_future_cf, initial_investment)
        
    @staticmethod
    def bottom_up_ocf(net_income: float, depreciation: float) -> float:
        return float(net_income + depreciation)
        
    @staticmethod
    def top_down_ocf(sales: float, costs: float, taxes: float) -> float:
        return float(sales - costs - taxes)
        
    @staticmethod
    def tax_shield_ocf(sales: float, costs: float, depreciation: float, tax_rate: float) -> float:
        return float((sales - costs) * (1 - tax_rate) + (depreciation * tax_rate))

    # ==========================================
    # CHAPTER 10 & 11: RISK, RETURN, CAPM
    # ==========================================
    @classmethod
    def dividend_yield(cls, next_dividend: float, current_price: float) -> float:
        return cls.safe_div(next_dividend, current_price)

    @staticmethod
    def arithmetic_average_return(returns: List[float]) -> float:
        if not returns:
            return np.nan
        return float(sum(returns) / len(returns))
        
    @staticmethod
    def geometric_average_return(returns: List[float]) -> float:
        if not returns:
            return np.nan
        try:
            product = np.prod([1 + r for r in returns])
            return float(product ** (1 / len(returns)) - 1)
        except Exception:
            return np.nan

    @staticmethod
    def expected_return_capm(risk_free_rate: float, beta: float, expected_market_return: float) -> float:
        return float(risk_free_rate + beta * (expected_market_return - risk_free_rate))

    # ==========================================
    # CHAPTER 12 & 14: WACC & CAPITAL STRUCTURE
    # ==========================================
    @classmethod
    def weighted_average_cost_of_capital(cls, equity_val: float, debt_val: float, cost_of_equity: float, cost_of_debt: float, corporate_tax_rate: float) -> float:
        v = equity_val + debt_val
        we = cls.safe_div(equity_val, v)
        wd = cls.safe_div(debt_val, v)
        
        if pd.isna(we) or pd.isna(wd):
            return np.nan
            
        return float((we * cost_of_equity) + (wd * cost_of_debt * (1 - corporate_tax_rate)))

    @staticmethod
    def mm_proposition_2_no_taxes(r0: float, cost_of_debt: float, debt_val: float, equity_val: float) -> float:
        """MM Proposition II (No Taxes): Rs = R0 + (B/S)*(R0 - Rb)"""
        if equity_val == 0:
            return np.nan
        return float(r0 + (debt_val / equity_val) * (r0 - cost_of_debt))

    # ==========================================
    # CHAPTER 17: OPTIONS PRICING
    # ==========================================
    @staticmethod
    def black_scholes_call(S: float, E: float, t: float, R: float, sigma: float) -> float:
        """
        S: Current stock price, E: Exercise price, t: Time to expiration (years),
        R: Risk-free rate (continuous), sigma: Volatility (standard dev)
        """
        if any(x <= 0 for x in [S, E, t, sigma]):
            return np.nan
            
        try:
            d1 = (np.log(S / E) + (R + (sigma ** 2) / 2) * t) / (sigma * np.sqrt(t))
            d2 = d1 - sigma * np.sqrt(t)
            call_price = S * norm.cdf(d1) - E * np.exp(-R * t) * norm.cdf(d2)
            return float(call_price)
        except Exception:
            return np.nan

    @staticmethod
    def put_call_parity_put_value(call_price: float, S: float, E: float, t: float, R: float) -> float:
        """P = C + PV(E) - S"""
        try:
            pv_E = E * np.exp(-R * t)
            return float(call_price + pv_E - S)
        except Exception:
            return np.nan

    # ==========================================
    # CHAPTER 18 & 20: SHORT TERM & INTERNATIONAL
    # ==========================================
    @staticmethod
    def operating_cycle(inventory_period: float, accounts_receivable_period: float) -> float:
        return float(inventory_period + accounts_receivable_period)
        
    @staticmethod
    def cash_cycle(operating_cycle: float, accounts_payable_period: float) -> float:
        return float(operating_cycle - accounts_payable_period)
        
    @classmethod
    def absolute_purchasing_power_parity(cls, spot_rate: float, foreign_price: float, domestic_price: float) -> float:
        """Returns inferred spot rate based on absolute PPP"""
        return cls.safe_div(foreign_price, domestic_price)
        
    @classmethod
    def relative_purchasing_power_parity(cls, current_spot: float, domestic_inflation: float, foreign_inflation: float, periods: int) -> float:
        """Expected future spot rate under Relative PPP"""
        try:
            return float(current_spot * ((1 + foreign_inflation) / (1 + domestic_inflation)) ** periods)
        except Exception:
            return np.nan

    # ==========================================
    # BATCH PROCESSOR FOR CSV DATA
    # ==========================================
    def process_financial_dataset(self, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Vectorized execution of analytical metrics across the entire loaded dataset.
        Robust to missing columns and rows with zeroes to prevent UI failures.
        """
        if self.data.empty:
            raise ValueError("No data loaded. Please initialize with a valid CSV or DataFrame.")
        
        df = self.data.copy()

        # Handle column mappings if the CSV headers differ from standard names
        if column_mapping:
            df.rename(columns=column_mapping, inplace=True)
            
        # Helper lambda to wrap safe calculations
        def safe_apply(func, *args):
            try:
                # Check if all required columns exist in the dataframe
                if not all(arg in df.columns for arg in args):
                    return np.nan
                # Vectorized fallback
                return np.vectorize(func)(*[df[arg] for arg in args])
            except Exception:
                return np.nan

        # CHAPTER 3 Computations
        if 'Current Assets' in df.columns and 'Current Liabilities' in df.columns:
            df['Current Ratio'] = safe_apply(self.current_ratio, 'Current Assets', 'Current Liabilities')
            
            if 'Inventory' in df.columns:
                df['Quick Ratio'] = safe_apply(self.quick_ratio, 'Current Assets', 'Inventory', 'Current Liabilities')

        if 'Total Assets' in df.columns and 'Total Equity' in df.columns:
            df['Equity Multiplier'] = safe_apply(self.equity_multiplier, 'Total Assets', 'Total Equity')
            df['Total Debt Ratio'] = safe_apply(self.total_debt_ratio, 'Total Assets', 'Total Equity')
            
        if 'Net Income' in df.columns:
            if 'Sales' in df.columns:
                df['Profit Margin'] = safe_apply(self.profit_margin, 'Net Income', 'Sales')
            if 'Total Assets' in df.columns:
                df['ROA'] = safe_apply(self.return_on_assets, 'Net Income', 'Total Assets')
            if 'Total Equity' in df.columns:
                df['ROE'] = safe_apply(self.return_on_equity, 'Net Income', 'Total Equity')
            if 'Shares Outstanding' in df.columns:
                df['EPS'] = safe_apply(self.earnings_per_share, 'Net Income', 'Shares Outstanding')

        if 'Price Per Share' in df.columns and 'EPS' in df.columns:
            df['PE Ratio'] = safe_apply(self.price_earnings_ratio, 'Price Per Share', 'EPS')

        if 'EBIT' in df.columns and 'Interest' in df.columns:
            df['Times Interest Earned'] = safe_apply(self.times_interest_earned, 'EBIT', 'Interest')

        return df


# ==========================================
# USAGE EXAMPLE
# ==========================================
if __name__ == "__main__":
    
    # 1. Provide mock DataFrame representing CSV import
    mock_data = pd.DataFrame({
        'Company': ['Apple', 'Microsoft', 'Distressed Co'],
        'Current Assets': [100000, 80000, 1000],
        'Current Liabilities': [50000, 40000, 0], # Zero liability to test error handling
        'Inventory': [10000, 5000, 500],
        'Total Assets': [500000, 400000, 10000],
        'Total Equity': [250000, 300000, 0], # Zero equity
        'Net Income': [50000, 60000, -500],
        'Sales': [300000, 250000, 2000],
        'Price Per Share': [150, 200, 1],
        'Shares Outstanding': [4000, 5000, 1000],
        'EBIT': [60000, 70000, -100],
        'Interest': [5000, 2000, 0] # Zero interest
    })
    
    # 2. Initialize analyzer
    analyzer = FundamentalAnalyzer(mock_data)
    
    # 3. Process CSV Data logic
    results = analyzer.process_financial_dataset()
    print("--- Batch Processing Results with Error Handling ---")
    print(results[['Company', 'Current Ratio', 'Quick Ratio', 'ROE', 'PE Ratio', 'Times Interest Earned']])
    
    # 4. Independent Method Testing
    print("\n--- Independent Method Testing ---")
    bs_call = analyzer.black_scholes_call(S=50, E=49, t=199/365, R=0.07, sigma=0.473)
    print(f"Black-Scholes Call Option: ${bs_call:.2f}" if not pd.isna(bs_call) else "BS Call: Error/NaN")
    
    growth_rate = analyzer.sustainable_growth_rate(roe=0.264, plowback_ratio=0.666)
    print(f"Sustainable Growth Rate: {growth_rate:.2%}" if not pd.isna(growth_rate) else "Growth Rate: Error/NaN")
    
    cash_cycle = analyzer.cash_cycle(operating_cycle=90, accounts_payable_period=30)
    print(f"Cash Cycle (Days): {cash_cycle:.1f}" if not pd.isna(cash_cycle) else "Cash Cycle: Error/NaN")