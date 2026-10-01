from dataclasses import dataclass
import io
import math
import pandas as pd


@dataclass
class ModelInputs:
    horizon: int = 15
    starting_ctc: float = 18.0
    starting_cash: float = 110000.0
    annual_increment: float = 10.0
    switch_year: int = 5
    switch_hike: float = 30.0
    salary_mode: str = "Stated cash-in-hand growth"

    bonus_pct: float = 10.0
    basic_pct: float = 40.0
    employer_pf_pct: float = 12.0
    employee_pf_pct: float = 12.0
    gratuity_pct: float = 4.81
    standard_deduction: float = 75000.0

    family_expense_pct: float = 40.0
    expense_inflation: float = 5.0
    wife_contribution: float = 10000.0
    wife_separate_income: float = 25000.0
    include_wife_income_in_investments: bool = False

    enable_child_1: bool = True
    child1_start: int = 4
    child1_early: float = 5000.0
    child1_school_year: int = 7
    child1_school: float = 15000.0

    enable_child_2: bool = True
    child2_start: int = 8
    child2_early: float = 5000.0
    child2_school_year: int = 11
    child2_school: float = 15000.0
    school_inflation: float = 7.0

    education_loan: float = 24.0
    education_emi: float = 30000.0
    education_years: int = 10

    car_year: int = 5
    car_cost: float = 15.0
    car_down: float = 7.5
    car_rate: float = 9.0
    car_tenure: int = 5
    car_maintenance: float = 60000.0
    car_maintenance_inflation: float = 7.0

    health_insurance: float = 30000.0
    health_inflation: float = 8.0
    medical_expense: float = 30000.0
    medical_inflation: float = 8.0
    vacation_expense: float = 60000.0
    vacation_inflation: float = 7.0

    investment_return: float = 8.0
    starting_investments: float = 0.0
    existing_assets: float = 0.0
    house_value: float = 0.0
    house_appreciation: float = 5.0

    wedding_year: int = 0
    wedding_cost: float = 0.0
    other_annual: float = 0.0
    other_inflation: float = 6.0


# AY 2026-27 new-regime slabs for a resident individual below 60.
# Tax is intentionally kept as a transparent function so it can be updated
# independently if Indian tax rules change.
NEW_REGIME_SLABS = [
    (400000, 0.00),
    (800000, 0.05),
    (1200000, 0.10),
    (1600000, 0.15),
    (2000000, 0.20),
    (2400000, 0.25),
    (float("inf"), 0.30),
]


def slab_tax(income: float) -> float:
    income = max(0.0, income)
    tax = 0.0
    lower = 0.0
    for upper, rate in NEW_REGIME_SLABS:
        taxable = max(0.0, min(income, upper) - lower)
        tax += taxable * rate
        if income <= upper:
            break
        lower = upper

    # AY 2026-27 new-regime rebate: up to ₹12 lakh total income.
    # For this planning model, the rebate is applied when taxable income
    # after standard deduction is <= ₹12 lakh.
    if income <= 1200000:
        tax = 0.0

    # Health & education cess.
    tax *= 1.04
    return tax


def car_emi(principal: float, annual_rate: float, years: int) -> float:
    if principal <= 0 or years <= 0:
        return 0.0
    r = annual_rate / 100 / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def fmt_lakh(x: float) -> float:
    return x / 100000.0


def format_inr(x: float) -> str:
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 10000000:
        return f"{sign}₹{x/10000000:.2f} Cr"
    if x >= 100000:
        return f"{sign}₹{x/100000:.2f} L"
    return f"{sign}₹{x:,.0f}"


def child_cost(year: int, start: int, early_monthly: float, school_year: int,
               school_monthly: float, school_inflation: float) -> float:
    if year < start:
        return 0.0
    if year < school_year:
        return early_monthly * 12
    years_since_school = year - school_year
    return school_monthly * 12 * (1 + school_inflation / 100) ** years_since_school


def run_model(p: ModelInputs):
    rows = []
    investment_corpus = p.starting_investments * 100000.0
    other_assets = p.existing_assets * 100000.0
    house_value = p.house_value * 100000.0

    base_family_expense = (
        p.starting_cash * 12 * p.family_expense_pct / 100.0
    )

    car_principal = max(0.0, (p.car_cost - p.car_down) * 100000.0)
    monthly_car_emi = car_emi(car_principal, p.car_rate, p.car_tenure)
    car_loan_end_year = p.car_year + p.car_tenure - 1

    for year in range(1, p.horizon + 1):
        # CTC progression: annual increment, with switch hike applied at the
        # beginning of Year (switch_year + 1).
        ctc = p.starting_ctc * 100000.0 * (1 + p.annual_increment / 100) ** (year - 1)
        if p.switch_year and year > p.switch_year:
            ctc *= (1 + p.switch_hike / 100.0)

        basic = ctc * p.basic_pct / 100.0
        employer_pf = basic * p.employer_pf_pct / 100.0
        gratuity = basic * p.gratuity_pct / 100.0
        bonus = ctc * p.bonus_pct / 100.0

        # Gross cash compensation excludes employer-only PF and gratuity.
        gross_salary = max(0.0, ctc - employer_pf - gratuity)
        taxable_salary = max(0.0, gross_salary - p.standard_deduction)
        tax = slab_tax(taxable_salary)
        employee_pf = basic * p.employee_pf_pct / 100.0

        detailed_net_annual = max(
            0.0, gross_salary - employee_pf - tax
        )
        detailed_net_monthly = detailed_net_annual / 12.0

        stated_net_monthly = p.starting_cash * (
            ctc / (p.starting_ctc * 100000.0)
        )

        if p.salary_mode == "Detailed salary + tax model":
            net_salary_annual = detailed_net_annual
            net_salary_monthly = detailed_net_monthly
        else:
            net_salary_monthly = stated_net_monthly
            net_salary_annual = stated_net_monthly * 12.0

        family_expenses = base_family_expense * (
            1 + p.expense_inflation / 100.0
        ) ** (year - 1)

        child1 = (
            child_cost(
                year, p.child1_start, p.child1_early,
                p.child1_school_year, p.child1_school, p.school_inflation
            )
            if p.enable_child_1 else 0.0
        )
        child2 = (
            child_cost(
                year, p.child2_start, p.child2_early,
                p.child2_school_year, p.child2_school, p.school_inflation
            )
            if p.enable_child_2 else 0.0
        )
        child_expenses = child1 + child2

        education_emi = (
            p.education_emi * 12.0
            if year <= p.education_years else 0.0
        )

        current_car_emi = (
            monthly_car_emi * 12.0
            if p.car_year > 0 and p.car_year <= year <= car_loan_end_year
            else 0.0
        )
        car_down_payment = (
            p.car_down * 100000.0 if year == p.car_year and p.car_year > 0 else 0.0
        )

        car_maint = (
            p.car_maintenance
            * (1 + p.car_maintenance_inflation / 100.0) ** max(0, year - p.car_year)
            if p.car_year > 0 and year >= p.car_year
            else 0.0
        )
        health = p.health_insurance * (
            1 + p.health_inflation / 100.0
        ) ** (year - 1)
        medical = p.medical_expense * (
            1 + p.medical_inflation / 100.0
        ) ** (year - 1)
        vacation = p.vacation_expense * (
            1 + p.vacation_inflation / 100.0
        ) ** (year - 1)
        other_costs = p.other_annual * (
            1 + p.other_inflation / 100.0
        ) ** (year - 1)
        one_off = p.wedding_cost * 100000.0 if year == p.wedding_year else 0.0

        wife_contribution_annual = p.wife_contribution * 12.0
        wife_separate_annual = p.wife_separate_income * 12.0

        total_outflows = (
            family_expenses
            + child_expenses
            + education_emi
            + current_car_emi
            + car_down_payment
            + car_maint
            + health
            + medical
            + vacation
            + other_costs
            + one_off
        )

        annual_income_for_cashflow = net_salary_annual + wife_contribution_annual
        annual_surplus = annual_income_for_cashflow - total_outflows

        if p.include_wife_income_in_investments:
            annual_surplus += wife_separate_annual

        # Negative surplus means the household needs to draw down existing
        # investment liquidity. Corpus is never allowed to become negative;
        # the negative amount is separately tracked as a funding gap.
        funding_gap = max(0.0, -annual_surplus)
        invested = max(0.0, annual_surplus)

        # Annual compounding with contributions assumed at year-end.
        investment_corpus = investment_corpus * (1 + p.investment_return / 100.0)
        investment_corpus += invested

        house_value = (
            house_value * (1 + p.house_appreciation / 100.0)
            if house_value > 0 else 0.0
        )

        # Other assets are kept constant unless user adds them as a starting
        # asset; this avoids inventing appreciation for unspecified assets.
        net_worth = investment_corpus + house_value + other_assets

        savings_rate = (
            invested / annual_income_for_cashflow * 100.0
            if annual_income_for_cashflow > 0 else 0.0
        )

        rows.append({
            "Year": year,
            "CTC": ctc,
            "Basic Salary": basic,
            "Employer PF": employer_pf,
            "Gratuity Provision": gratuity,
            "Bonus": bonus,
            "Gross Cash Compensation": gross_salary,
            "Taxable Salary": taxable_salary,
            "Employee PF": employee_pf,
            "Income Tax": tax,
            "Net Salary": net_salary_annual,
            "Monthly Net Salary": net_salary_monthly,
            "Detailed Net Salary (Tax Model)": detailed_net_annual,
            "Family Expenses": family_expenses,
            "Child Expenses": child_expenses,
            "Education Loan EMI": education_emi,
            "Car EMI": current_car_emi,
            "Car Down Payment": car_down_payment,
            "Car Maintenance & Insurance": car_maint,
            "Health Insurance": health,
            "Medical": medical,
            "Vacations": vacation,
            "Other Costs": other_costs,
            "One-off Cost": one_off,
            "Wife Contribution": wife_contribution_annual,
            "Wife Separate Income": wife_separate_annual,
            "Annual Surplus": annual_surplus,
            "Invested This Year": invested,
            "Funding Gap": funding_gap,
            "Investment Corpus": investment_corpus,
            "House Value": house_value,
            "Other Assets": other_assets,
            "Net Worth": net_worth,
            "Savings Rate (%)": savings_rate,
        })

    df = pd.DataFrame(rows)

    final = df.iloc[-1]
    total_invested = float(df["Invested This Year"].sum())
    total_tax = float(df["Income Tax"].sum())
    total_employee_pf = float(df["Employee PF"].sum())
    investment_gains = float(final["Investment Corpus"] - p.starting_investments * 100000.0 - total_invested)

    emergency_target = (
        (base_family_expense + p.education_emi * 12 + p.health_insurance + p.medical_expense)
        * (6 / 12)
    )

    summary = {
        "final_ctc": float(final["CTC"]),
        "final_monthly_net": float(final["Monthly Net Salary"]),
        "final_investment_corpus": float(final["Investment Corpus"]),
        "final_net_worth": float(final["Net Worth"]),
        "total_invested": total_invested,
        "investment_gains": investment_gains,
        "total_tax": total_tax,
        "total_employee_pf": total_employee_pf,
        "emergency_target": emergency_target,
    }
    return df, summary


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
