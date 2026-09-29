# Fortune Credit: Seasonal Credit Risk Analysis

## Project Overview
This project is an interactive data analysis dashboard built as a case study for Fortune Credit, a licensed Digital Credit Provider and microfinance institution in Kenya. It analyzes loan portfolio data to identify credit risk patterns, specifically focusing on the impact of seasonal harvest cycles on smallholder farmer loan repayments.

## Business Problem
Microfinance institutions often face elevated default rates in agricultural lending. A key operational challenge is determining the optimal time to disburse loans to farmers. Disbursing too early or too late in the agricultural cycle can create liquidity gaps for the borrower, leading to missed repayments and increased risk for the lender.

## Illustrative Observations (Proof of Concept)
Note: This analysis uses a small mock dataset (n=10 total loans, n=7 farmer loans) to demonstrate the analytical pipeline. These findings are illustrative and require real historical data to establish statistical significance or causal effects.

By engineering a "Harvest Gap" feature (the number of days between loan disbursement and expected harvest), this project isolates timing risk in agricultural loans. 

Mock Dataset Observations:
1. Risk by Segment: Default rates vary across customer types, highlighting the need for tailored risk models for Boda Riders, Traders, and Farmers.
2. The Repayment Pattern: In this mock dataset, both farmer loans issued 31 to 90 days before harvest were repaid (2/2, 100%), compared with two of five loans issued over 90 days before harvest (2/5, 40%). There were zero observations in the 0 to 30 day window. More representative data, including actual loan due dates and actual repayment dates, is needed to evaluate if repayment truly aligns with harvest income.

---

## Code Explanation & Technical Implementation

This project was built to demonstrate end-to-end data engineering and analysis skills, with a strong focus on analytical correctness and reproducibility.

### 1. Centralized Data Processing & Validation
A shared `data_processing.py` module enforces the DRY (Don't Repeat Yourself) principle, ensuring consistency across scripts. It includes robust validation checks for:
- Missing required columns and duplicate `Loan_ID`s.
- Negative loan amounts, invalid dates, and negative harvest gaps.
- Unexpected repayment statuses.
- Imputation Flagging: Missing `Loan_Amount` values are imputed with the median. A new `Imputed_Loan_Amount` boolean column flags these rows to maintain transparency, as median imputation preserves the median but can shift the mean.

### 2. Numeric Harvest Timing & SQL Logic
A critical fix was applied to keep the `Days_to_Harvest` column strictly numeric. Missing values for non-agricultural loans (Boda Riders, Traders) are represented as `NaN`, which translates to `NULL` in SQLite. Display labels (e.g., '31-90 Days') are created separately within the SQL `CASE WHEN` statement. This prevents text-sorting bugs (where "100" incorrectly sorts before "30") and allows clean SQL filtering using `IS NOT NULL`.

### 3. Repayment Metrics & Visualization
- Metric Definition: "Late" loans are now explicitly tracked and displayed separately. This ensures that a 0% default rate is not misinterpreted as a 100% repayment rate, providing an accurate picture of portfolio health.
- Interactive Dashboard (`app.py`): Uses native Streamlit charts to plot only the `Default_Rate` percentage, with raw loan counts displayed separately in a data table below the chart.
- Static Reporting (`clean_data.py`): Uses Matplotlib and OpenPyXL to generate high-resolution PNG charts and export structured Excel reports for offline stakeholder review.

---

## Technology Stack
- Python: Core programming language for backend logic.
- Pandas: Data manipulation, missing value handling, and datetime calculations.
- SQLite: In-memory relational database for executing intermediate-level SQL queries.
- Streamlit: Framework for building the interactive, browser-based data application.
- Matplotlib & OpenPyXL: Libraries for generating static visualizations and Excel exports.

---

## Project Structure
```text
Fortune-Credit-Data-Analysis-/
├── app.py                      # Main Streamlit web application
├── clean_data.py               # Script for static chart generation and Excel export
├── data_processing.py          # Centralized data loading, validation, and cleaning logic
├── data/
│   └── fortune_harvest_data.csv # Raw mock dataset
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## How to Run Locally

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/toxidity-18/Fortune-Credit-Data-Analysis-.git
   cd Fortune-Credit-Data-Analysis-
   ```
2. Create a virtual environment (recommended) and install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Option A: Run the Interactive Dashboard
   ```bash
   streamlit run app.py
   ```
4. Option B: Generate Static Reports
   ```bash
   python clean_data.py
   ```
   (This will generate chart1_default_rate.png, chart2_farmer_sweet_spot.png, and Fortune_Credit_Dashboard.xlsx in your root directory).

---

## Live Demo
[Live interactive dashboard](https://fortunecreditriskanalysis.streamlit.app/)
```