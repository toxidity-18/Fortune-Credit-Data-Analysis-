
# Fortune Credit: Seasonal Credit Risk Analysis

## Project Overview
This project is an interactive data analysis dashboard built as a case study for Fortune Credit, a licensed Digital Credit Provider and microfinance institution in Kenya. It analyzes loan portfolio data to identify credit risk patterns, specifically focusing on the impact of seasonal harvest cycles on smallholder farmer loan repayments.

## Business Problem
Microfinance institutions often face elevated default rates in agricultural lending. A key operational challenge is determining the optimal time to disburse loans to farmers. Disbursing too early or too late in the agricultural cycle can create liquidity gaps for the borrower, leading to missed repayments and increased risk for the lender.

## Illustrative Observations (Proof of Concept)
Note: This analysis uses a small mock dataset (n=10 total loans, n=7 farmer loans) to demonstrate the analytical pipeline. These findings are illustrative and require real historical data to establish statistical significance or causal effects. This limitation is now explicitly stated in both the interactive dashboard and the exported static reports.

By engineering a "Harvest Gap" feature (the number of days between loan disbursement and expected harvest), this project isolates timing risk in agricultural loans. 

Mock Dataset Observations:
1. Risk by Segment: Default rates vary across customer types, highlighting the need for tailored risk models for Boda Riders, Traders, and Farmers.
2. The Repayment Pattern: In this mock dataset, both farmer loans issued 31 to 90 days before harvest were repaid (2/2, 100%), compared with two of five loans issued over 90 days before harvest (2/5, 40%). There were zero observations in the 0 to 30 day window. More representative data, including actual loan due dates and actual repayment dates, is needed to evaluate if repayment truly aligns with harvest income.

---

## Code Explanation & Technical Implementation

This project was built to demonstrate end-to-end data engineering and analysis skills, with a strong focus on analytical correctness, enforced validation, and reproducibility.

### 1. Centralized Data Processing & Strict Validation
A shared `data_processing.py` module enforces the DRY (Don't Repeat Yourself) principle. Unlike previous iterations that only issued warnings, the current implementation enforces strict validation and quarantines invalid data:
- Identity Validation: Rows with missing or duplicate `Loan_ID`s are explicitly dropped, not retained.
- Safe Amount Parsing: Formatted currency strings (e.g., "KES 1,000") are safely parsed using regex. Negative or invalid amounts are quarantined, and median imputation is calculated strictly from valid, non-negative values.
- Status Normalization: Unexpected repayment statuses are quarantined into an "Unknown" category and explicitly excluded from rate denominators to prevent silent distortion of metrics.
- Exclusion Transparency: An `exclusion_counts` dictionary tracks exactly how many rows are dropped or quarantined for each reason. These counts are exposed in the Streamlit sidebar and exported as a "Validation Summary" sheet in the static Excel report.

### 2. Numeric Harvest Timing & Explicit Policies
The `Days_to_Harvest` column remains strictly numeric, with missing values represented as `NaN` (translating to `NULL` in SQLite). 
- Negative Harvest Gaps: Loans issued after the expected harvest (negative days) are now explicitly categorized into an "After Harvest" group, preventing them from being incorrectly grouped into the "0-30 Days" bucket.
- Invalid Date Handling: Malformed dates for farmers are explicitly flagged and excluded from timing analysis, clearly distinguishing them from legitimate non-agricultural loans that naturally lack a harvest date.

### 3. Repayment Metrics, Visualization, and Caching
- Metric Definition: "Late" loans are explicitly tracked. SQL denominators are filtered to only include known, valid statuses ('Repaid', 'Defaulted', 'Late'), ensuring accurate rate calculations.
- Interactive Dashboard (`app.py`): Uses native Streamlit charts to plot only the `Default_Rate` percentage, with raw loan counts displayed separately in a data table. Cache invalidation is now tied to the source CSV file's modification time, ensuring the dashboard never displays stale data after a file update.
- Static Reporting (`clean_data.py`): Uses Matplotlib and OpenPyXL to generate high-resolution PNG charts and structured Excel reports, including the validation summary.

---

## Technology Stack
- Python: Core programming language for backend logic.
- Pandas: Data manipulation, safe parsing, missing value handling, and datetime calculations.
- SQLite: In-memory relational database for executing intermediate-level SQL queries.
- Streamlit: Framework for building the interactive, browser-based data application.
- Matplotlib & OpenPyXL: Libraries for generating static visualizations and Excel exports.
- Dependencies: Versions are now explicitly pinned in `requirements.txt` to ensure reproducible environments.

---

## Project Structure
```text
Fortune-Credit-Data-Analysis-/
├── app.py                      # Main Streamlit web application
├── clean_data.py               # Script for static chart generation and Excel export
├── data_processing.py          # Centralized data loading, strict validation, and cleaning logic
├── data/
│   └── fortune_harvest_data.csv # Raw mock dataset
├── requirements.txt            # Pinned Python dependencies
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
   (This will generate chart1_default_rate.png, chart2_farmer_sweet_spot.png, and Fortune_Credit_Dashboard.xlsx in your root directory, including the Validation Summary sheet).

---

## Live Demo
[Live interactive dashboard](https://fortunecreditriskanalysis.streamlit.app/)
```