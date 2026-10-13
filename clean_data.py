import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from data_processing import load_and_clean_data

# ==========================================
# PART 1: LOAD AND VALIDATE DATA
# ==========================================
# Unpack both the cleaned dataframe and the exclusion counts dictionary
df, exclusion_counts = load_and_clean_data('data/fortune_harvest_data.csv')

print("--- Data Validation & Exclusion Summary ---")
for key, value in exclusion_counts.items():
    print(f" - {key.replace('_', ' ').title()}: {value}")
print("-------------------------------------------\n")

# ==========================================
# PART 2: SQL ANALYSIS
# ==========================================
conn = sqlite3.connect(':memory:')
df.to_sql('loans', conn, index=False, if_exists='replace')

# Query 1: Default and Late rates by customer segment
# FIXED (Finding 3 & 4): Filter denominator to only include known, valid statuses
query_1 = """
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

# Query 2: Repayment rate based on harvest timing (Farmers only)
# FIXED (Finding 1): Explicitly handle negative gaps as 'After Harvest'
query_2 = """
SELECT 
    CASE 
        WHEN Days_to_Harvest < 0 THEN 'After Harvest'
        WHEN Days_to_Harvest <= 30 THEN '0-30 Days'
        WHEN Days_to_Harvest BETWEEN 31 AND 90 THEN '31-90 Days'
        ELSE 'Over 90 Days' 
    END as Timing,
    COUNT(*) as Total_Farmer_Loans,
    SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) as Total_Repaid,
    ROUND(100.0 * SUM(CASE WHEN Repayment_Status = 'Repaid' THEN 1 ELSE 0 END) / COUNT(*), 1) as Repay_Rate
FROM loans 
WHERE Customer_Type = 'Farmer' AND Days_to_Harvest IS NOT NULL
GROUP BY Timing 
ORDER BY 
    CASE Timing 
        WHEN 'After Harvest' THEN 1
        WHEN '0-30 Days' THEN 2
        WHEN '31-90 Days' THEN 3
        ELSE 4 
    END ASC;
"""

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
plt.ylim(0, 100)
plt.savefig('chart1_default_rate.png', dpi=150, bbox_inches='tight')
plt.close()

# Chart 2: The Farmer "Sweet Spot" (Now includes After Harvest)
plt.figure(figsize=(8, 5))
plt.bar(res2['Timing'], res2['Repay_Rate'], color='#428bca')
plt.title('Fortune Credit: Farmer Repayment Rate by Loan Timing')
plt.ylabel('Repayment Rate (%)')
plt.xlabel('Days Before Harvest')
plt.ylim(0, 100)
plt.savefig('chart2_farmer_sweet_spot.png', dpi=150, bbox_inches='tight')
plt.close()

# Save to Excel
with pd.ExcelWriter('Fortune_Credit_Dashboard.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Raw Data', index=False)
    res1.to_excel(writer, sheet_name='SQL - Default Rates', index=False)
    res2.to_excel(writer, sheet_name='SQL - Farmer Sweet Spot', index=False)
    
    # FIXED (Finding 6): Expose exclusion counts in the static report as well
    exclusion_df = pd.DataFrame(list(exclusion_counts.items()), columns=['Exclusion Type', 'Count'])
    exclusion_df.to_excel(writer, sheet_name='Validation Summary', index=False)

print("✅ Dashboard and charts created successfully.")
print("\n--- SQL Query 2 Results (Harvest Timing) ---")
print(res2)