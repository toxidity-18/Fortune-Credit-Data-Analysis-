# Fortune Credit: Seasonal Credit Risk Analysis

## Project Overview
This project is an interactive data analysis dashboard built as a case study for **Fortune Credit**, a licensed Digital Credit Provider and microfinance institution in Kenya. It analyzes loan portfolio data to identify credit risk patterns, specifically focusing on the impact of seasonal harvest cycles on smallholder farmer loan repayments.

## Business Problem
Microfinance institutions often face elevated default rates in agricultural lending. A key operational challenge is determining the optimal time to disburse loans to farmers to ensure they have the cash flow to repay when the loan matures. Disbursing too early or too late in the agricultural cycle can lead to liquidity gaps for the borrower and increased risk for the lender.

## Solution and Key Insights
By engineering a "Harvest Gap" feature (the number of days between loan disbursement and expected harvest), this project isolates the timing risk in agricultural loans. 

**Key Findings:**
1. **Risk by Segment:** Default rates vary significantly across customer types, requiring tailored risk models for Boda Riders, Traders, and Farmers.
2. **The Repayment "Sweet Spot":** Farmer loans disbursed **31 to 90 days before harvest** demonstrate a significantly higher repayment rate compared to loans given too early (90+ days) or too late (0-30 days).

---

## Code Explanation & Technical Implementation

This project was built to demonstrate end-to-end data engineering and analysis skills. Below is a breakdown of the technical logic:

### 1. Data Cleaning & Feature Engineering (Pandas)
Real-world financial data is rarely clean. The `load_and_clean_data()` function handles several edge cases:
* **Missing Value Imputation:** Instead of dropping rows with missing `Loan_Amount` values, the code calculates the median loan amount and fills the gaps. This preserves dataset integrity without skewing the mean.
* **Text Standardization:** Human entry errors (e.g., "repayed") are standardized to "Repaid" using `.replace()`.
* **Mixed-Type Resolution:** The `Days_to_Harvest` column initially contained both floats (e.g., `90.0`) and strings (`'Non-Ag'` for non-agricultural loans). This caused PyArrow serialization errors in Streamlit. The issue was resolved by explicitly casting the column to a string type (`astype(str)`) after calculation, ensuring seamless dataframe rendering.
* **Date Manipulation:** String dates are converted to `datetime` objects to accurately calculate the day difference between disbursement and expected harvest.

### 2. In-Memory SQL Analysis (SQLite)
Rather than relying solely on Pandas for aggregation, the filtered data is loaded into an in-memory SQLite database (`sqlite3.connect(':memory:')`). This demonstrates the ability to write production-style SQL queries:
* **Default Rate Calculation:** Uses a `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` pattern to count defaults and calculate the percentage dynamically per customer segment.
* **Categorical Binning:** Uses a `CASE WHEN` statement to group continuous numerical data (`Days_to_Harvest`) into actionable business buckets ('0-30 Days', '31-90 Days', '90+ Days').

### 3. Interactive Dashboard (Streamlit)
The `app.py` file wraps the analysis in a user-friendly web interface:
* **Performance Optimization:** The `@st.cache_data` decorator is applied to the data loading function. This prevents the app from re-reading the CSV and recalculating dates on every user interaction, ensuring sub-second load times.
* **Safe Data Filtering:** When applying sidebar filters, the code uses `.copy()` on the filtered dataframe. This prevents the common Pandas `SettingWithCopyWarning` and ensures data integrity.
* **Memory Management:** After rendering charts with `st.pyplot()`, `plt.close(fig)` is explicitly called. This prevents Matplotlib from holding figures in memory, which is a common cause of crashes in long-running Streamlit apps.

---

## Technology Stack
* **Python:** Core programming language for backend logic.
* **Pandas:** Data manipulation, missing value handling, and datetime calculations.
* **SQLite:** In-memory relational database for executing intermediate-level SQL queries.
* **Streamlit:** Framework for building the interactive, browser-based data application.
* **Matplotlib:** Library for generating clean, professional data visualizations.

---

## Project Structure
```text
Fortune-Credit-Data-Analysis/
├── app.py                      # Main Streamlit web application
├── clean_data.py               # Initial data cleaning and SQL analysis script
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
   cd Fortune-Credit-Data-Analysis
   ```
2. Create a virtual environment (recommended) and install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
4. Open your web browser and navigate to `http://localhost:8501`.

---

## Live Demo
[Click here to view the live interactive dashboard](INSERT_YOUR_STREAMLIT_LINK_HERE)

---