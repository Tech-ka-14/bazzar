def calculate_cooke_ratio(eligible_tier_capital: float, risk_capital_requirement: float) -> float:
    """
    Calculates the Cooke Ratio (Capital Adequacy Ratio).
    By Basel standards, this ratio traditionally must remain above 8%.
    """
    if risk_capital_requirement <= 0:
        raise ValueError("Risk capital requirement must be greater than zero.")
        
    solvency_ratio = eligible_tier_capital / risk_capital_requirement
    return solvency_ratio

def check_regulatory_compliance(eligible_tier_capital: float, risk_capital_requirement: float, 
                                minimum_ratio: float = 0.08) -> dict:
    """
    Evaluates if a financial institution meets the minimum regulatory solvency requirements.
    """
    ratio = calculate_cooke_ratio(eligible_tier_capital, risk_capital_requirement)
    
    is_compliant = ratio >= minimum_ratio
    excess_capital = eligible_tier_capital - (risk_capital_requirement * minimum_ratio)
    
    return {
        "Cooke_Ratio": ratio,
        "Is_Compliant": is_compliant,
        "Excess_Capital_Buffer": excess_capital
    }

# --- Final Example ---
# A bank has calculated its total Minimum Risk Capital (MRC) using its internal VaR models
total_mrc = 500_000_000  # $500 Million

# The bank holds actual liquid equity/reserves (Tier 1 & 2 Capital)
eligible_capital = 65_000_000  # $65 Million

compliance_report = check_regulatory_compliance(eligible_capital, total_mrc, minimum_ratio=0.08)

print(f"Solvency Ratio: {compliance_report['Cooke_Ratio']*100:.2f}%")
print(f"Compliant: {compliance_report['Is_Compliant']}")
if compliance_report['Is_Compliant']:
    print(f"Excess Buffer: ${compliance_report['Excess_Capital_Buffer']:,.2f}")
else:
    print(f"Capital Shortfall: ${abs(compliance_report['Excess_Capital_Buffer']):,.2f}")