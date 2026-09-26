import streamlit as st
import pandas as pd
import sqlite3

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Fortune Credit Risk Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Fortune Credit: Seasonal Credit Risk Analysis")
st.markdown("An interactive dashboard analyzing loan portfolio risk and harvest timing.")

# ==========================================
# 2. DATA LOADING AND CLEANING
# ==========================================
@st.cache_data
def load_and_clean_data():
    """
    Loads the raw CSV data and performs necessary cleaning operations.
    Cached to prevent reloading and recalculating on every user interaction.
    """
    data = pd.read_csv('data/fortune_harvest_data.csv')
    data['Repayment_Status'] = data['Repayment_Status'].replace('repayed', 'Repaid')
    median_loan = data['Loan_Amount'].median()
    data['Loan_Amount'] = data['Loan_Amount'].fillna(median_loan)
    data['Expected_Harvest_Date'] = data['Expected_Harvest_Date'].replace('N/A', pd.NA)
    data['Disbursement_Date'] = pd.to_datetime(data['Disbursement_Date'])
    data['Expected_Harvest_Date'] = pd.to_datetime(data['Expected_Harvest_Date'])
    data['Days_to_Harvest'] = (data['Expected_Harvest_Date'] - data['Disbursement_Date']).dt.days
    data['Days_to_Harvest'] = data['Days_to_Harvest'].fillna('Non-Ag')
    data['Days_to_Harvest'] = data['Days_to_Harvest'].astype(str)
    return data

loan_data = load_and_clean_data()

# ==========================================
# 3. USER INTERFACE & FILTERING
# ==========================================
st.sidebar.header("Filter Data")
customer_filter = st.sidebar.selectbox(
    "Select Customer Type", 
    ['All', 'Farmer', 'Boda Rider', 'Trader']
)

if customer_filter != 'All':
    filtered_data = loan_data[loan_data['Customer_Type'] == customer_filter].copy()
else:
    filtered_data = loan_data.copy()

# ==========================================
# 4. KEY PERFORMANCE INDICATORS (KPIs)
# ==========================================
col1, col2, col3 = st.columns(3)

total_loans = len(filtered_data)
total_defaults = len(filtered_data[filtered_data['Repayment_Status'] == 'Defaulted'])
avg_loan_amount = filtered_data['Loan_Amount'].mean()

col1.metric("Total Loans Analyzed", total_loans)
col2.metric("Total Defaults", total_defaults)
col3.metric("Avg Loan Amount", f"KES {avg_loan_amount:,.0f}")

st.markdown("---")

# ==========================================
# 5. SQL ANALYSIS LOGIC
# ==========================================
conn = sqlite3.connect(':memory:')
filtered_data.to_sql('loans', conn, index=False, if_exists='replace')

query_default_rate = """
    SELECT 
        Customer_Type, 
        COUNT(*) as Total_Loans,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Defaulted' THEN 1 ELSE 0 END) / COUNT(*), 1) as Default_Rate
    FROM loans 
    GROUP BY Customer_Type 
    ORDER BY Default_Rate DESC;
"""

query_harvest_timing = """
    SELECT 
        CASE 
            WHEN Days_to_Harvest <= 30 THEN '0-30 Days'
            WHEN Days_to_Harvest BETWEEN 31 AND 90 THEN '31-90 Days (Sweet Spot)'
            ELSE '90+ Days' 
        END as Harvest_Timing,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) / COUNT(*), 1) as Repayment_Rate
    FROM loans 
    WHERE Customer_Type = 'Farmer' AND Days_to_Harvest != 'Non-Ag'
    GROUP BY Harvest_Timing 
    ORDER BY Repayment_Rate DESC;
"""

df_default_rate = pd.read_sql_query(query_default_rate, conn)
df_harvest_timing = pd.read_sql_query(query_harvest_timing, conn)
conn.close()

# ==========================================
# 6. DATA VISUALIZATION (NATIVE STREAMLIT CHARTS)
# ==========================================
chart_col1, chart_col2 = st.columns(2)

# Chart 1: Default Rate by Customer Type
with chart_col1:
    st.subheader("Default Rate by Customer Type")
    # Set Customer_Type as the index for the chart
    chart_data_1 = df_default_rate.set_index('Customer_Type')
    st.bar_chart(chart_data_1)

# Chart 2: Farmer Repayment Sweet Spot
with chart_col2:
    st.subheader("Farmer Repayment Rate by Loan Timing")
    if not df_harvest_timing.empty:
        chart_data_2 = df_harvest_timing.set_index('Harvest_Timing')
        st.bar_chart(chart_data_2)
    else:
        st.info("Select 'Farmer' or 'All' in the sidebar to view the harvest timing analysis.")

# ==========================================
# 7. RAW DATA DISPLAY
# ==========================================
st.markdown("---")
st.subheader("Raw Data View")
st.dataframe(filtered_data, width="stretch")