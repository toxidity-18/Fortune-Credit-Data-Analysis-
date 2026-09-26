import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# ==========================================
# PART 1: LOAD AND CLEAN DATA
# ==========================================
df = pd.read_csv('data/fortune_harvest_data.csv')
df['Repayment_Status'] = df['Repayment_Status'].replace('repayed', 'Repaid')
median_loan = df['Loan_Amount'].median()
df['Loan_Amount'] = df['Loan_Amount'].fillna(median_loan)
df['Expected_Harvest_Date'] = df['Expected_Harvest_Date'].replace('N/A', pd.NA)

df['Disbursement_Date'] = pd.to_datetime(df['Disbursement_Date'])
df['Expected_Harvest_Date'] = pd.to_datetime(df['Expected_Harvest_Date'])
df['Days_to_Harvest'] = (df['Expected_Harvest_Date'] - df['Disbursement_Date']).dt.days
df['Days_to_Harvest'] = df['Days_to_Harvest'].fillna('Non-Ag')

# ==========================================
# PART 2: SQL ANALYSIS
# ==========================================
conn = sqlite3.connect(':memory:')
df.to_sql('loans', conn, index=False, if_exists='replace')

query_1 = """
SELECT Customer_Type, COUNT(*) as Total, 
       ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Defaulted' THEN 1 ELSE 0 END) / COUNT(*), 1) as Default_Rate
FROM loans GROUP BY Customer_Type ORDER BY Default_Rate DESC;"""

query_2 = """
SELECT CASE WHEN Days_to_Harvest <= 30 THEN '0-30 Days'
            WHEN Days_to_Harvest BETWEEN 31 AND 90 THEN '31-90 Days (Sweet Spot)'
            ELSE '90+ Days' END as Timing,
       ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) / COUNT(*), 1) as Repay_Rate
FROM loans WHERE Customer_Type = 'Farmer' AND Days_to_Harvest != 'Non-Ag'
GROUP BY Timing ORDER BY Repay_Rate DESC;"""

res1 = pd.read_sql_query(query_1, conn)
res2 = pd.read_sql_query(query_2, conn)
conn.close()

# ==========================================
# PART 3: BUILD CHARTS & EXCEL DASHBOARD
# ==========================================

# Chart 1: Default Rate by Customer Type
plt.figure(figsize=(8, 5))
plt.bar(res1['Customer_Type'], res1['Default_Rate'], color=['#d9534f', '#f0ad4e', '#5cb85c'])
plt.title('Fortune Credit: Default Rate by Customer Type')
plt.ylabel('Default Rate (%)')
plt.xlabel('Customer Type')
plt.savefig('chart1_default_rate.png', dpi=150, bbox_inches='tight')
plt.close()

# Chart 2: The Farmer "Sweet Spot"
plt.figure(figsize=(8, 5))
plt.bar(res2['Timing'], res2['Repay_Rate'], color='#428bca')
plt.title('Fortune Credit: Farmer Repayment Rate by Loan Timing')
plt.ylabel('Repayment Rate (%)')
plt.xlabel('Days Before Harvest')
plt.savefig('chart2_farmer_sweet_spot.png', dpi=150, bbox_inches='tight')
plt.close()

# Save to a beautiful Excel file
with pd.ExcelWriter('Fortune_Credit_Dashboard.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Raw Data', index=False)
    res1.to_excel(writer, sheet_name='SQL - Default Rates', index=False)
    res2.to_excel(writer, sheet_name='SQL - Farmer Sweet Spot', index=False)

print("Dashboard and charts created successfully.")