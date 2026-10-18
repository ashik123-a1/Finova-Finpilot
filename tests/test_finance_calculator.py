"""
Unit Tests for Deterministic Financial Calculation Engine.
Verifies integer minor units precision, rounding rules, zero floating point contamination,
and exact financial formulas.
"""

from decimal import Decimal
import pytest
from src.core.money import Money
from src.finance.calculator import FinancialCalculator


def test_money_precision_and_zero_float_contamination():
    """Verifies that Money prevents float inaccuracies (e.g. 0.1 + 0.2)."""
    m1 = Money.from_major("0.10")  # 10 minor
    m2 = Money.from_major("0.20")  # 20 minor
    m3 = m1 + m2
    assert m3.amount_minor == 30
    assert m3.amount_major == Decimal("0.30")
    assert m3.format() == "0.30 BDT"

    # Multiplication with rounding half up
    m4 = Money.from_major("10.55")
    m5 = m4 * Decimal("1.5")  # 1055 * 1.5 = 1582.5 -> 1583 minor units
    assert m5.amount_minor == 1583
    assert m5.format() == "15.83 BDT"


def test_profit_and_loss_calculation():
    """Verifies Revenue, COGS, Gross Profit, Expenses, Net Profit and Margins."""
    sales = [100_000_00, 50_000_00]       # 150,000 BDT
    cogs = [60_000_00, 30_000_00]         # 90,000 BDT
    expenses = [15_000_00, 10_000_00]     # 25,000 BDT

    pl = FinancialCalculator.calculate_profit_and_loss(sales, cogs, expenses)

    assert pl.revenue_minor == 150_000_00
    assert pl.cogs_minor == 90_000_00
    assert pl.gross_profit_minor == 60_000_00
    assert pl.operating_expenses_minor == 25_000_00
    assert pl.net_profit_minor == 35_000_00
    # Gross margin = 60,000 / 150,000 = 40.0%
    assert pl.gross_margin_pct == 40.0
    # Net margin = 35,000 / 150,000 = 23.33%
    assert pl.net_margin_pct == 23.33


def test_cash_flow_calculation():
    """Verifies Cash Flow Inflow/Outflow and Closing Balance."""
    opening = 50_000_00
    inflows = [20_000_00, 15_000_00]
    outflows = [10_000_00, 5_000_00]

    cf = FinancialCalculator.calculate_cash_flow(opening, inflows, outflows)
    assert cf.cash_inflows_minor == 35_000_00
    assert cf.cash_outflows_minor == 15_000_00
    assert cf.net_cash_flow_minor == 20_000_00
    assert cf.closing_balance_minor == 70_000_00


def test_loan_reducing_vs_flat_rate_comparison():
    """
    Verifies that Flat Rate interest produces significantly higher total payment
    and higher effective APR than Reducing Balance (EMI).
    """
    principal = 100_000_00  # 100,000 BDT
    rate_pct = 12.0         # 12% annual
    tenure_months = 12

    comp = FinancialCalculator.calculate_loan_comparison(
        principal_minor=principal,
        annual_interest_rate_pct=rate_pct,
        tenure_months=tenure_months,
        processing_fee_bps=100,  # 1% = 1,000 BDT
    )

    assert comp.processing_fee_minor == 1_000_00
    # In reducing balance, monthly EMI is ~8,885 BDT, total interest ~6,619 BDT
    assert comp.reducing_total_interest_minor < comp.flat_total_interest_minor
    # In flat rate: 12% on 100,000 for 1 yr = 12,000 BDT total interest!
    assert comp.flat_total_interest_minor == 12_000_00
    # Penalty of flat rate = ~5,381 BDT extra cost
    assert comp.flat_rate_penalty_minor > 5_000_00
    # Effective APR of flat rate is roughly ~22%
    assert comp.effective_apr_flat_pct > comp.effective_apr_reducing_pct


def test_break_even_analysis():
    """Verifies Break-even units and break-even revenue calculation."""
    fixed_costs = 50_000_00          # 50,000 BDT fixed overhead
    selling_price = 500_00           # 500 BDT selling price
    variable_cost = 300_00           # 300 BDT variable cost

    # Contribution margin = 200 BDT
    # Break even units = 50,000 / 200 = 250 units
    res = FinancialCalculator.calculate_break_even(fixed_costs, selling_price, variable_cost)
    assert res.contribution_margin_per_unit_minor == 200_00
    assert res.break_even_units == 250
    assert res.break_even_revenue_minor == 125_000_00


def test_roi_and_payback():
    """Verifies ROI % and simple payback period."""
    initial_inv = 100_000_00
    cash_inflows = [40_000_00, 40_000_00, 40_000_00]  # Total 120,000 BDT

    res = FinancialCalculator.calculate_roi_and_payback(initial_inv, cash_inflows)
    assert res.net_profit_minor == 20_000_00
    assert res.roi_pct == 20.0
    # Year 1: 40k, Year 2: 80k, Year 3: need 20k of 40k = 2.5 years
    assert res.simple_payback_period_years == 2.5
