# 15-Year Salary, Cash Flow & Net Worth Planner

A Streamlit app that projects:

- CTC and salary progression
- Career switch and switch hike
- Salary structure: basic, bonus, employer PF and gratuity
- Employee PF and estimated income tax
- Monthly and annual net salary
- Family expenses and inflation
- Wife contribution and optional additional income
- One- or two-child education costs
- Education-loan EMI
- Car purchase, down payment, EMI, maintenance and insurance
- Health insurance
- Medical expenses
- Vacations/travel
- Other annual discretionary expenses
- One-off major expenses
- Annual surplus/savings
- Investment corpus at a selected return
- House value appreciation
- Overall projected net worth
- CSV download of the complete 15-year cash-flow model

## Files

```text
salary-corpus-streamlit/
├── app.py
├── model.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```

## Deploy on Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload all files while preserving the `.streamlit/config.toml` folder.
3. Go to Streamlit Community Cloud.
4. Create a new app.
5. Select your GitHub repository.
6. Set the main file to `app.py`.
7. Deploy.

No API key or secret is required.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Model methodology

### CTC progression

Year 1 starts at the entered CTC.

Each subsequent year receives the annual increment. If a career switch is selected, the switch hike is applied from the year immediately after the switch year.

Example:

- Starting CTC = ₹18L
- Annual increment = 10%
- Switch at end of Year 5
- Switch hike = 30%

Then Year 6 is calculated as the Year-5 salary progression followed by the 30% switch uplift.

### Two net-salary modes

**1. Stated cash-in-hand growth**

This preserves the original planning model. Starting monthly cash-in-hand is scaled in proportion to CTC.

This is the default because it reproduces the original ₹1.10 lakh/month starting cash-in-hand assumption without double-counting tax.

**2. Detailed salary + tax model**

The app estimates:

- Basic salary
- Employer PF
- Gratuity provision
- Bonus
- Gross cash compensation
- Employee PF
- Taxable salary
- Income tax
- Detailed net salary

The tax function is deliberately isolated in `model.py` so the slabs can be updated when tax rules change.

### Investment calculation

Annual surplus is invested at the selected annual return. Contributions are assumed to happen at the end of each year.

Therefore the model is a planning projection rather than a monthly SIP simulation.

### Car loan

Car EMI is calculated using the standard reducing-balance EMI formula.

### Net worth

Projected net worth is:

```text
Investment Corpus
+ House Value
+ Starting Other Assets
```

The model does not automatically assign appreciation to unspecified assets.

## Important modelling caveats

This is a planning model, not a tax filing engine or investment recommendation.

Tax rules, PF rules, salary structures, bonus treatment, gratuity eligibility, inflation, investment returns and personal expenses can change.

The model intentionally exposes major assumptions in the sidebar so the user can stress-test them.

Before making real financial decisions, verify salary structure and tax treatment with the employer/payroll team or a qualified tax professional.
