import streamlit as st
import pandas as pd
import plotly.express as px

from model import (
    ModelInputs,
    run_model,
    format_inr,
    to_csv_bytes,
)

st.set_page_config(
    page_title="15-Year Salary & Wealth Planner",
    page_icon="📈",
    layout="wide",
)

st.title("📈 15-Year Salary, Cash Flow & Net Worth Planner")
st.caption(
    "Interactive projection tool for salary growth, household cash flow, debt, "
    "investments, retirement-style corpus and scenario planning. "
    "All figures are projections, not financial advice."
)

with st.sidebar:
    st.header("Core career assumptions")
    starting_ctc = st.number_input("Starting CTC (₹ lakh)", 1.0, 500.0, 18.0, 0.5)
    starting_cash = st.number_input(
        "Starting monthly cash-in-hand (₹)", 0, 5000000, 110000, 5000
    )
    annual_increment = st.number_input("Annual salary increment (%)", 0.0, 50.0, 10.0, 0.5)
    switch_year = st.number_input("Switch at end of Year", 0, 14, 5, 1)
    switch_hike = st.number_input("Switch hike (%)", 0.0, 100.0, 30.0, 1.0)
    horizon = st.slider("Projection horizon (years)", 5, 30, 15)

    st.header("Salary structure")
    salary_mode = st.radio(
        "Net-salary method",
        ["Stated cash-in-hand growth", "Detailed salary + tax model"],
        index=0,
    )
    bonus_pct = st.number_input("Annual bonus / variable pay (% of CTC)", 0.0, 50.0, 10.0, 0.5)
    basic_pct = st.number_input("Basic salary (% of CTC)", 20.0, 70.0, 40.0, 1.0)
    employer_pf_pct = st.number_input("Employer PF (% of basic)", 0.0, 20.0, 12.0, 0.5)
    employee_pf_pct = st.number_input("Employee PF (% of basic)", 0.0, 20.0, 12.0, 0.5)
    gratuity_pct = st.number_input("Gratuity provision (% of basic)", 0.0, 10.0, 4.81, 0.01)
    standard_deduction = st.number_input("Standard deduction (₹)", 0, 500000, 75000, 5000)

    st.header("Family & living costs")
    family_expense_pct = st.number_input(
        "Family expenses as % of starting annual net salary", 0.0, 100.0, 40.0, 1.0
    )
    expense_inflation = st.number_input("General expense inflation (%)", 0.0, 20.0, 5.0, 0.5)
    wife_contribution = st.number_input("Wife contribution / month (₹)", 0, 1000000, 10000, 1000)
    wife_separate_income = st.number_input(
        "Wife's remaining income / month (₹)", 0, 1000000, 25000, 1000
    )
    include_wife_income_in_investments = st.checkbox(
        "Invest wife's remaining income", value=False
    )

    st.header("Children")
    enable_child_1 = st.checkbox("Child 1", value=True)
    child1_start = st.number_input("Child 1 expense starts in Year", 1, 30, 4, 1)
    child1_early = st.number_input("Child 1 expense / month before school (₹)", 0, 500000, 5000, 500)
    child1_school_year = st.number_input("Child 1 school starts in Year", 1, 30, 7, 1)
    child1_school = st.number_input("Child 1 school expense / month (₹)", 0, 1000000, 15000, 500)
    school_inflation = st.number_input("School fee inflation (%)", 0.0, 25.0, 7.0, 0.5)

    enable_child_2 = st.checkbox("Child 2", value=True)
    child2_start = st.number_input("Child 2 expense starts in Year", 1, 30, 8, 1)
    child2_early = st.number_input("Child 2 expense / month before school (₹)", 0, 500000, 5000, 500)
    child2_school_year = st.number_input("Child 2 school starts in Year", 1, 30, 11, 1)
    child2_school = st.number_input("Child 2 school expense / month (₹)", 0, 1000000, 15000, 500)

    st.header("Education loan")
    education_loan = st.number_input("Education loan principal (₹ lakh)", 0.0, 500.0, 24.0, 0.5)
    education_emi = st.number_input("Education loan EMI / month (₹)", 0, 2000000, 30000, 1000)
    education_years = st.number_input("Education loan duration (years)", 0, 30, 10, 1)

    st.header("Car")
    car_year = st.number_input("Car purchase Year", 0, 30, 5, 1)
    car_cost = st.number_input("Car cost (₹ lakh)", 0.0, 500.0, 15.0, 0.5)
    car_down = st.number_input("Car down payment (₹ lakh)", 0.0, 500.0, 7.5, 0.5)
    car_rate = st.number_input("Car loan interest (%)", 0.0, 30.0, 9.0, 0.25)
    car_tenure = st.number_input("Car loan tenure (years)", 1, 15, 5, 1)
    car_maintenance = st.number_input(
        "Initial annual car maintenance + insurance (₹)", 0, 1000000, 60000, 5000
    )
    car_maintenance_inflation = st.number_input(
        "Car maintenance/insurance inflation (%)", 0.0, 25.0, 7.0, 0.5
    )

    st.header("Other protection & lifestyle")
    health_insurance = st.number_input(
        "Initial annual health insurance (₹)", 0, 1000000, 30000, 5000
    )
    health_inflation = st.number_input("Insurance inflation (%)", 0.0, 25.0, 8.0, 0.5)
    medical_expense = st.number_input(
        "Initial annual medical / healthcare budget (₹)", 0, 2000000, 30000, 5000
    )
    medical_inflation = st.number_input("Medical inflation (%)", 0.0, 25.0, 8.0, 0.5)
    vacation_expense = st.number_input(
        "Initial annual vacation/travel budget (₹)", 0, 5000000, 60000, 5000
    )
    vacation_inflation = st.number_input("Vacation inflation (%)", 0.0, 25.0, 7.0, 0.5)

    st.header("Investments & assets")
    investment_return = st.number_input("Investment return (%)", 0.0, 30.0, 8.0, 0.25)
    starting_investments = st.number_input(
        "Starting investment corpus (₹ lakh)", 0.0, 10000.0, 0.0, 1.0
    )
    existing_assets = st.number_input(
        "Starting other assets (₹ lakh)", 0.0, 100000.0, 0.0, 1.0
    )
    house_value = st.number_input(
        "Starting owned-house value (₹ lakh)", 0.0, 100000.0, 0.0, 1.0
    )
    house_appreciation = st.number_input("House appreciation (%)", -10.0, 20.0, 5.0, 0.5)

    st.header("One-off / discretionary costs")
    wedding_year = st.number_input("Wedding / major one-off Year (0 = none)", 0, 30, 0, 1)
    wedding_cost = st.number_input("Wedding / one-off cost (₹ lakh)", 0.0, 1000.0, 0.0, 0.5)
    other_annual = st.number_input("Other annual discretionary costs (₹)", 0, 10000000, 0, 5000)
    other_inflation = st.number_input("Other-cost inflation (%)", 0.0, 25.0, 6.0, 0.5)

    st.header("Advanced")
    emergency_fund_months = st.number_input(
        "Emergency fund target (months of current core expenses)", 0, 24, 6, 1
    )
    include_emergency_target = st.checkbox(
        "Show emergency-fund target", value=True
    )

inputs = ModelInputs(
    horizon=horizon,
    starting_ctc=starting_ctc,
    starting_cash=starting_cash,
    annual_increment=annual_increment,
    switch_year=switch_year,
    switch_hike=switch_hike,
    salary_mode=salary_mode,
    bonus_pct=bonus_pct,
    basic_pct=basic_pct,
    employer_pf_pct=employer_pf_pct,
    employee_pf_pct=employee_pf_pct,
    gratuity_pct=gratuity_pct,
    standard_deduction=standard_deduction,
    family_expense_pct=family_expense_pct,
    expense_inflation=expense_inflation,
    wife_contribution=wife_contribution,
    wife_separate_income=wife_separate_income,
    include_wife_income_in_investments=include_wife_income_in_investments,
    enable_child_1=enable_child_1,
    child1_start=child1_start,
    child1_early=child1_early,
    child1_school_year=child1_school_year,
    child1_school=child1_school,
    enable_child_2=enable_child_2,
    child2_start=child2_start,
    child2_early=child2_early,
    child2_school_year=child2_school_year,
    child2_school=child2_school,
    school_inflation=school_inflation,
    education_loan=education_loan,
    education_emi=education_emi,
    education_years=education_years,
    car_year=car_year,
    car_cost=car_cost,
    car_down=car_down,
    car_rate=car_rate,
    car_tenure=car_tenure,
    car_maintenance=car_maintenance,
    car_maintenance_inflation=car_maintenance_inflation,
    health_insurance=health_insurance,
    health_inflation=health_inflation,
    medical_expense=medical_expense,
    medical_inflation=medical_inflation,
    vacation_expense=vacation_expense,
    vacation_inflation=vacation_inflation,
    investment_return=investment_return,
    starting_investments=starting_investments,
    existing_assets=existing_assets,
    house_value=house_value,
    house_appreciation=house_appreciation,
    wedding_year=wedding_year,
    wedding_cost=wedding_cost,
    other_annual=other_annual,
    other_inflation=other_inflation,
)

df, summary = run_model(inputs)

st.subheader("15-Year Projection")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Final CTC", format_inr(summary["final_ctc"]))
c2.metric("Final monthly net salary", format_inr(summary["final_monthly_net"]))
c3.metric("Investment corpus", format_inr(summary["final_investment_corpus"]))
c4.metric("Net worth", format_inr(summary["final_net_worth"]))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Total invested savings", format_inr(summary["total_invested"]))
c6.metric("Investment gains", format_inr(summary["investment_gains"]))
c7.metric("Total taxes", format_inr(summary["total_tax"]))
c8.metric("Total employee PF", format_inr(summary["total_employee_pf"]))

if include_emergency_target:
    st.info(
        f"Indicative emergency-fund target based on Year 1 core expenses: "
        f"{format_inr(summary['emergency_target'])}"
    )

st.markdown("### Cash-flow table")
display_cols = [
    "Year", "CTC", "Net Salary", "Bonus", "Employee PF", "Income Tax",
    "Family Expenses", "Child Expenses", "Education Loan EMI", "Car EMI",
    "Car Down Payment", "Car Maintenance & Insurance", "Health Insurance",
    "Medical", "Vacations", "Other Costs", "One-off Cost",
    "Wife Contribution", "Wife Separate Income", "Annual Surplus",
    "Investment Corpus", "House Value", "Net Worth"
]
table = df[display_cols].copy()
for col in table.columns:
    if col != "Year":
        table[col] = table[col].map(format_inr)
st.dataframe(table, use_container_width=True, hide_index=True)

st.markdown("### Salary trajectory")
fig1 = px.line(
    df, x="Year", y=["CTC", "Net Salary"], markers=True,
    title="CTC vs Net Salary"
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### Annual cash flow")
fig2 = px.bar(
    df, x="Year",
    y=["Family Expenses", "Child Expenses", "Education Loan EMI", "Car EMI",
       "Car Maintenance & Insurance", "Health Insurance", "Medical",
       "Vacations", "Other Costs", "One-off Cost"],
    title="Annual household outflows",
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Wealth accumulation")
fig3 = px.line(
    df, x="Year",
    y=["Investment Corpus", "Net Worth"],
    markers=True,
    title="Investment Corpus and Net Worth"
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("### Savings rate")
fig4 = px.line(
    df, x="Year", y="Savings Rate (%)", markers=True,
    title="Annual savings rate"
)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("### Key observations")
obs = [
    f"Your projected CTC grows from {format_inr(df.iloc[0]['CTC'])} to {format_inr(df.iloc[-1]['CTC'])}.",
    f"Your annual surplus ranges from {format_inr(df.iloc[0]['Annual Surplus'])} in Year 1 to {format_inr(df.iloc[-1]['Annual Surplus'])} in Year {horizon}.",
    f"Investment corpus reaches {format_inr(df.iloc[-1]['Investment Corpus'])} by Year {horizon}, assuming the selected return and annual investment timing.",
    f"Projected net worth reaches {format_inr(df.iloc[-1]['Net Worth'])}, including the modeled house and other starting assets.",
]
for item in obs:
    st.write("• " + item)

csv = to_csv_bytes(df)
st.download_button(
    "⬇️ Download 15-year projection as CSV",
    data=csv,
    file_name="15_year_salary_cashflow_projection.csv",
    mime="text/csv",
)

st.caption(
    "Tax engine uses the AY 2026-27 new-regime slab structure as a configurable "
    "starting point. Tax rules can change; review before using for actual tax planning."
)
