import streamlit as st
import pandas as pd
import sqlite3
import os
from data_processing import load_and_clean_data

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
st.info("Note: This dashboard uses a simulated dataset to demonstrate analytical logic. Findings are illustrative.")

# ==========================================
# 2. DATA LOADING AND CACHING (Fixed Finding 6)
# ==========================================
@st.cache_data
def get_clean_data(file_path: str, file_mtime: float):
    """
    Loads and cleans data. 
    Cache is invalidated if the file modification time changes (Fixes Finding 6).
    """
    return load_and_clean_data(file_path)

file_path = 'data/fortune_harvest_data.csv'
# Get the last modification time of the file to use as a cache key
file_mtime = os.path.getmtime(file_path)

# Unpack the tuple returned by our updated data_processing function
loan_data, exclusion_counts = get_clean_data(file_path, file_mtime)

# ==========================================
# 3. SIDEBAR: DATA QUALITY & EXCLUSIONS (Fixed Findings 2, 3, 4)
# ==========================================
st.sidebar.header("Data Quality & Exclusions")
st.sidebar.markdown("Rows excluded or quarantined during validation:")
for key, value in exclusion_counts.items():
    st.sidebar.metric(key.replace('_', ' ').title(), value)

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
col1, col2, col3, col4 = st.columns(4)

total_loans = len(filtered_data)
total_repaid = len(filtered_data[filtered_data['Repayment_Status'] == 'Repaid'])
total_late = len(filtered_data[filtered_data['Repayment_Status'] == 'Late'])
total_defaulted = len(filtered_data[filtered_data['Repayment_Status'] == 'Defaulted'])

col1.metric("Total Valid Loans", total_loans)
col2.metric("Repaid", total_repaid)
col3.metric("Late", total_late)
col4.metric("Defaulted", total_defaulted)

st.markdown("---")

# ==========================================
# 5. SQL ANALYSIS LOGIC
# ==========================================
conn = sqlite3.connect(':memory:')
filtered_data.to_sql('loans', conn, index=False, if_exists='replace')

# Query 1: Default and Late rates by customer segment
# Added WHERE clause to ensure denominator only includes known, valid statuses (Finding 3)
query_default_late = """
    SELECT 
        Customer_Type, 
        COUNT(*) as Total_Loans,
        SUM(CASE WHEN Repayment_Status = 'Defaulted' THEN 1 ELSE 0 END) as Total_Defaults,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Defaulted' THEN 1 ELSE 0 END) / COUNT(*), 1) as Default_Rate,
        SUM(CASE WHEN Repayment_Status = 'Late' THEN 1 ELSE 0 END) as Total_Late,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Late' THEN 1 ELSE 0 END) / COUNT(*), 1) as Late_Rate
    FROM loans 
    WHERE Repayment_Status IN ('Repaid', 'Defaulted', 'Late')
    GROUP BY Customer_Type 
    ORDER BY Default_Rate DESC;
"""

# Query 2: Repayment rate based on harvest timing (Fixed Finding 1: Negative gaps)
query_harvest_timing = """
    SELECT 
        CASE 
            WHEN Days_to_Harvest < 0 THEN 'After Harvest'
            WHEN Days_to_Harvest <= 30 THEN '0-30 Days'
            WHEN Days_to_Harvest BETWEEN 31 AND 90 THEN '31-90 Days'
            ELSE 'Over 90 Days' 
        END as Harvest_Timing,
        COUNT(*) as Total_Farmer_Loans,
        SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) as Total_Repaid,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) / COUNT(*), 1) as Repayment_Rate
    FROM loans 
    WHERE Customer_Type = 'Farmer' 
      AND Days_to_Harvest IS NOT NULL
    GROUP BY Harvest_Timing 
    ORDER BY 
        CASE Harvest_Timing 
            WHEN 'After Harvest' THEN 0
            WHEN '0-30 Days' THEN 1 
            WHEN '31-90 Days' THEN 2 
            ELSE 3 
        END ASC;
"""

df_default_late = pd.read_sql_query(query_default_late, conn)
df_harvest_timing = pd.read_sql_query(query_harvest_timing, conn)
conn.close()

# ==========================================
# 6. DATA VISUALIZATION
# ==========================================
chart_col1, chart_col2 = st.columns(2)

# Chart 1: Default Rate by Customer Type
with chart_col1:
    st.subheader("Default Rate by Customer Type")
    if not df_default_late.empty:
        chart_data_1 = df_default_late.set_index('Customer_Type')[['Default_Rate']]
        st.bar_chart(chart_data_1, y_label="Default Rate (%)", height=300)
        
        st.markdown("**Loan Counts by Status:**")
        st.dataframe(
            df_default_late[['Customer_Type', 'Total_Loans', 'Total_Defaults', 'Total_Late']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No valid data available for the selected filter.")

# Chart 2: Farmer Repayment Sweet Spot
with chart_col2:
    st.subheader("Farmer Repayment Rate by Loan Timing")
    if not df_harvest_timing.empty:
        chart_data_2 = df_harvest_timing.set_index('Harvest_Timing')[['Repayment_Rate']]
        st.bar_chart(chart_data_2, y_label="Repayment Rate (%)", height=300)
        
        st.markdown("**Sample Sizes & Repayment Counts:**")
        st.dataframe(
            df_harvest_timing[['Harvest_Timing', 'Total_Farmer_Loans', 'Total_Repaid']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Select 'Farmer' or 'All' in the sidebar to view the harvest timing analysis.")

# ==========================================
# 7. RAW DATA DISPLAY
# ==========================================
st.markdown("---")
st.subheader("Raw Data View (Including Quarantined/Flagged Rows)")
st.dataframe(filtered_data, width="stretch")