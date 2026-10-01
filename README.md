# Fortune Credit: Seasonal Credit Risk Analysis

## Project Overview

A data analysis case study exploring repayment patterns in agricultural lending using simulated loan data.

The project examines whether the timing of a farmer's loan relative to the expected harvest is associated with different repayment patterns.

> **Note:** This is an independent case study using a small simulated dataset. It is not based on Fortune Credit's internal data.

## Business Question

**Could the timing of an agricultural loan relative to the expected harvest be associated with different repayment patterns?**

To explore this, I created a **Harvest Gap** feature representing the number of days between loan disbursement and the expected harvest date.

## Key Observations

The dataset contains:

- **10 total loans**
- **7 farmer loans**
- **2 farmer loans** in the 31–90 day group
- **5 farmer loans** in the 90+ day group
- **0 farmer loans** in the 0–30 day group

In this small dataset:

- 31–90 days: **2/2 loans repaid (100%)**
- 90+ days: **2/5 loans repaid (40%)**

These are descriptive observations only. The dataset is too small to establish statistical significance or causal relationships.

## Analysis

The project uses:

- **Python & Pandas** for data cleaning and preparation
- **SQLite & SQL** for analysis and aggregation
- **Streamlit** for the interactive dashboard
- **Matplotlib** for visualizations
- **OpenPyXL** for Excel reporting

The data processing includes validation of:

- Missing and duplicate loan IDs
- Invalid dates
- Negative loan amounts
- Invalid harvest gaps
- Unexpected repayment statuses

`Days_to_Harvest` is kept as a numeric field, while timing groups such as `31–90 Days` are created separately for reporting and visualization.

Repayment outcomes are also separated into **Repaid, Late, and Defaulted** rather than treating them as the same outcome.

## Project Structure

```text
Fortune-Credit-Data-Analysis-/
├── app.py
├── clean_data.py
├── data_processing.py
├── data/
│   └── fortune_harvest_data.csv
├── requirements.txt
└── README.md
```

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/toxidity-18/Fortune-Credit-Data-Analysis-.git
cd Fortune-Credit-Data-Analysis-
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the dashboard

```bash
streamlit run app.py
```

### 4. Generate static reports

```bash
python clean_data.py
```

## AI-Assisted Development

AI-assisted development tools were used throughout the project to help with implementation, debugging, understanding unfamiliar concepts, and improving the code.

I reviewed, tested, and modified the generated implementations while working through the analytical and technical issues identified during development.

## Limitations

The dataset is intentionally small and simulated. The results should not be used to make real lending decisions.

A larger historical dataset with actual disbursement dates, harvest dates, repayment dates, loan terms, and customer information would be required for more meaningful analysis.

## What I Learned

This project helped me strengthen my understanding of:

- Data cleaning and validation
- SQL-based analysis
- Feature engineering
- Financial data analysis
- Data visualization
- Analytical reasoning
- Reproducible project setup
- Communicating findings without overstating the evidence

## Links

**Live Dashboard:** https://fortunecreditriskanalysis.streamlit.app/

**GitHub Repository:** https://github.com/toxidity-18/Fortune-Credit-Data-Analysis-
