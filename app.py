import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

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
    # Load raw data
    data = pd.read_csv('data/fortune_harvest_data.csv')
    
    # Standardize text values
    data['Repayment_Status'] = data['Repayment_Status'].replace('repayed', 'Repaid')
    
    # Handle missing numerical data using the median to avoid skewing
    median_loan = data['Loan_Amount'].median()
    data['Loan_Amount'] = data['Loan_Amount'].fillna(median_loan)
    
    # Handle missing categorical data
    data['Expected_Harvest_Date'] = data['Expected_Harvest_Date'].replace('N/A', pd.NA)
    
    # Convert string dates to datetime objects for calculation
    data['Disbursement_Date'] = pd.to_datetime(data['Disbursement_Date'])
    data['Expected_Harvest_Date'] = pd.to_datetime(data['Expected_Harvest_Date'])
    
    # Calculate the days between loan disbursement and expected harvest
    data['Days_to_Harvest'] = (data['Expected_Harvest_Date'] - data['Disbursement_Date']).dt.days
    
    # Label non-agricultural loans appropriately
    data['Days_to_Harvest'] = data['Days_to_Harvest'].fillna('Non-Ag')
    
    # CRITICAL FIX: Explicitly cast the column to string. 
    # This prevents PyArrow from crashing when it sees a mix of numbers and the string 'Non-Ag'
    data['Days_to_Harvest'] = data['Days_to_Harvest'].astype(str)
    
    return data

# Execute data loading
loan_data = load_and_clean_data()

# ==========================================
# 3. USER INTERFACE & FILTERING
# ==========================================
st.sidebar.header("Filter Data")
customer_filter = st.sidebar.selectbox(
    "Select Customer Type", 
    ['All', 'Farmer', 'Boda Rider', 'Trader']
)

# Apply filter. Using .copy() prevents Pandas SettingWithCopyWarning.
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
# Create an in-memory SQLite database for the filtered data
conn = sqlite3.connect(':memory:')
filtered_data.to_sql('loans', conn, index=False, if_exists='replace')

# Query 1: Default rate by customer segment
query_default_rate = """
    SELECT 
        Customer_Type, 
        COUNT(*) as Total_Loans,
        ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Defaulted' THEN 1 ELSE 0 END) / COUNT(*), 1) as Default_Rate
    FROM loans 
    GROUP BY Customer_Type 
    ORDER BY Default_Rate DESC;
"""

# Query 2: Repayment rate based on harvest timing (Farmers only)
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

# Execute queries
df_default_rate = pd.read_sql_query(query_default_rate, conn)
df_harvest_timing = pd.read_sql_query(query_harvest_timing, conn)
conn.close()

# ==========================================
# 6. DATA VISUALIZATION
# ==========================================
chart_col1, chart_col2 = st.columns(2)

# Chart 1: Default Rate by Customer Type
with chart_col1:
    st.subheader("Default Rate by Customer Type")
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(df_default_rate['Customer_Type'], df_default_rate['Default_Rate'], color=['#d9534f', '#f0ad4e', '#5cb85c'])
    ax1.set_ylabel('Default Rate (%)')
    ax1.set_xlabel('Customer Type')
    ax1.set_ylim(0, 100) # Keep Y-axis consistent
    st.pyplot(fig1)
    plt.close(fig1) # Close figure to free memory

# Chart 2: Farmer Repayment Sweet Spot
with chart_col2:
    st.subheader("Farmer Repayment Rate by Loan Timing")
    
    if not df_harvest_timing.empty:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.bar(df_harvest_timing['Harvest_Timing'], df_harvest_timing['Repayment_Rate'], color='#428bca')
        ax2.set_ylabel('Repayment Rate (%)')
        ax2.set_xlabel('Days Before Harvest')
        ax2.set_ylim(0, 100)
        st.pyplot(fig2)
        plt.close(fig2) # Close figure to free memory
    else:
        st.info("Select 'Farmer' or 'All' in the sidebar to view the harvest timing analysis.")

# ==========================================
# 7. RAW DATA DISPLAY
# ==========================================
st.markdown("---")
st.subheader("Raw Data View")
# CRITICAL FIX: Updated deprecated 'use_container_width' to 'width="stretch"'
st.dataframe(filtered_data, width="stretch")