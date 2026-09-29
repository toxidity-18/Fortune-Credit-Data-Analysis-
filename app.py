import streamlit as st
import pandas as pd
import sqlite3
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

# ==========================================
# 2. DATA LOADING AND CLEANING
# ==========================================
@st.cache_data
def get_clean_data():
    """
    Loads and cleans data using the centralized, validated function.
    """
    return load_and_clean_data('data/fortune_harvest_data.csv')

loan_data = get_clean_data()

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
# 4. KEY PERFORMANCE INDICATORS (KPIs) - FIXED (Point 4)
# ==========================================
col1, col2, col3, col4 = st.columns(4)

total_loans = len(filtered_data)
total_defaults = len(filtered_data[filtered_data['Repayment_Status'] == 'Defaulted'])
total_late = len(filtered_data[filtered_data['Repayment_Status'] == 'Late'])
total_repaid = len(filtered_data[filtered_data['Repayment_Status'] == 'Repaid'])

col1.metric("Total Loans", total_loans)
col2.metric("Repaid", total_repaid)
col3.metric("Late", total_late)
col4.metric("Defaulted", total_defaults)

st.markdown("---")

# ==========================================
# 5. SQL ANALYSIS LOGIC
# ==========================================
conn = sqlite3.connect(':memory:')
filtered_data.to_sql('loans', conn, index=False, if_exists='replace')

# Query 1: Default and Late rates by customer segment (Fixed Point 4)
query_default_late = """
    SELECT 
        Customer_Type, 
        COUNT(*) as Total_Loans,
        SUM(CASE WHEN Repayment_Status = 'Defaulted' THEN 1 ELSE 0 END) as Total_Defaults,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Defaulted' THEN 1 ELSE 0 END) / COUNT(*), 1) as Default_Rate,
        SUM(CASE WHEN Repayment_Status = 'Late' THEN 1 ELSE 0 END) as Total_Late,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Late' THEN 1 ELSE 0 END) / COUNT(*), 1) as Late_Rate
    FROM loans 
    GROUP BY Customer_Type 
    ORDER BY Default_Rate DESC;
"""

# Query 2: Repayment rate based on harvest timing (Farmers only, numeric comparison)
query_harvest_timing = """
    SELECT 
        CASE 
            WHEN Days_to_Harvest <= 30 THEN '0-30 Days'
            WHEN Days_to_Harvest BETWEEN 31 AND 90 THEN '31-90 Days'
            ELSE 'Over 90 Days' 
        END as Harvest_Timing,
        COUNT(*) as Total_Farmer_Loans,
        SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) as Total_Repaid,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) / COUNT(*), 1) as Repayment_Rate
    FROM loans 
    WHERE Customer_Type = 'Farmer' AND Days_to_Harvest IS NOT NULL
    GROUP BY Harvest_Timing 
    ORDER BY 
        CASE Harvest_Timing 
            WHEN '0-30 Days' THEN 1 
            WHEN '31-90 Days' THEN 2 
            ELSE 3 
        END ASC;
"""

df_default_late = pd.read_sql_query(query_default_late, conn)
df_harvest_timing = pd.read_sql_query(query_harvest_timing, conn)
conn.close()

# ==========================================
# 6. DATA VISUALIZATION - FIXED (Point 3)
# ==========================================
chart_col1, chart_col2 = st.columns(2)

# Chart 1: Default Rate by Customer Type (Plotting ONLY the rate)
with chart_col1:
    st.subheader("Default Rate by Customer Type")
    # Set Customer_Type as the index, keep only the rate column for the chart
    chart_data_1 = df_default_late.set_index('Customer_Type')[['Default_Rate']]
    st.bar_chart(chart_data_1, y_label="Default Rate (%)", height=300)
    
    # Show counts separately in a clean table below the chart
    st.markdown("**Loan Counts by Status:**")
    st.dataframe(
        df_default_late[['Customer_Type', 'Total_Loans', 'Total_Defaults', 'Total_Late']], 
        use_container_width=True,
        hide_index=True
    )

# Chart 2: Farmer Repayment Sweet Spot
with chart_col2:
    st.subheader("Farmer Repayment Rate by Loan Timing")
    if not df_harvest_timing.empty:
        chart_data_2 = df_harvest_timing.set_index('Harvest_Timing')[['Repayment_Rate']]
        st.bar_chart(chart_data_2, y_label="Repayment Rate (%)", height=300)
        
        # Show sample sizes separately
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
st.subheader("Raw Data View")
st.dataframe(filtered_data, width="stretch")