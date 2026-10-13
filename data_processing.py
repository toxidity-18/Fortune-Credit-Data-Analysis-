import pandas as pd
import numpy as np
import warnings

def load_and_validate_data(filepath: str) -> tuple[pd.DataFrame, dict]:
    """
    Loads, strictly validates, and cleans the raw loan dataset.
    Returns a tuple: (cleaned_dataframe, validation_summary_dict)
    """
    # 1. Load Data
    df = pd.read_csv(filepath)
    initial_row_count = len(df)
    validation_summary = {
        "initial_rows": initial_row_count,
        "dropped_missing_id": 0,
        "dropped_duplicates": 0,
        "invalid_amounts_quarantined": 0,
        "unknown_statuses": 0,
        "invalid_farmer_dates": 0
    }

    # 2. STRICT VALIDATION & QUARANTINE
    
    # A. Loan ID: Must be non-blank. Drop missing. Drop exact duplicates (keep first).
    df = df.dropna(subset=['Loan_ID'])
    validation_summary["dropped_missing_id"] = initial_row_count - len(df)
    
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['Loan_ID'], keep='first')
    validation_summary["dropped_duplicates"] = before_dedup - len(df)

    # B. Loan Amount: Force numeric, handle strings like "KES 1,000", quarantine negatives/invalids
    # Remove currency symbols and commas, then convert
    df['Loan_Amount_Clean'] = df['Loan_Amount'].astype(str).str.replace(r'[^\d.]', '', regex=True)
    df['Loan_Amount_Numeric'] = pd.to_numeric(df['Loan_Amount_Clean'], errors='coerce')
    
    # Identify invalid amounts (NaN after conversion, or negative)
    invalid_amount_mask = df['Loan_Amount_Numeric'].isna() | (df['Loan_Amount_Numeric'] < 0)
    validation_summary["invalid_amounts_quarantined"] = invalid_amount_mask.sum()
    
    # Flag them, but keep the row (we will impute later, but we track the original state)
    df['Imputed_Loan_Amount'] = invalid_amount_mask | df['Loan_Amount'].isna()
    
    # Calculate median ONLY from valid, non-negative amounts
    valid_amounts = df.loc[~invalid_amount_mask, 'Loan_Amount_Numeric']
    median_loan = valid_amounts.median() if not valid_amounts.empty else 0.0
    
    # Apply imputation
    df['Loan_Amount'] = df['Loan_Amount_Numeric'].fillna(median_loan)
    df.loc[invalid_amount_mask, 'Loan_Amount'] = median_loan # Force impute the bad ones
    
    # Clean up helper columns
    df = df.drop(columns=['Loan_Amount_Clean', 'Loan_Amount_Numeric'])

    # C. Repayment Status: Normalize and quarantine unknowns
    valid_statuses = ['Repaid', 'Defaulted', 'Late']
    df['Repayment_Status'] = df['Repayment_Status'].astype(str).str.strip().str.title()
    
    # Fix specific known typos
    df['Repayment_Status'] = df['Repayment_Status'].replace('Repayed', 'Repaid')
    
    unknown_status_mask = ~df['Repayment_Status'].isin(valid_statuses)
    validation_summary["unknown_statuses"] = unknown_status_mask.sum()
    df.loc[unknown_status_mask, 'Repayment_Status'] = 'Unknown'

    # D. Dates: Coerce to datetime, track invalid farmer dates
    df['Disbursement_Date'] = pd.to_datetime(df['Disbursement_Date'], errors='coerce')
    df['Expected_Harvest_Date'] = pd.to_datetime(df['Expected_Harvest_Date'], errors='coerce')
    
    # A farmer MUST have a valid expected harvest date for timing analysis.
    # If Customer_Type is Farmer and Expected_Harvest_Date is NaT, it's an invalid date.
    farmer_invalid_date_mask = (df['Customer_Type'] == 'Farmer') & (df['Expected_Harvest_Date'].isna())
    validation_summary["invalid_farmer_dates"] = farmer_invalid_date_mask.sum()
    
    # Create a flag for this specific exclusion reason
    df['Exclusion_Reason'] = np.where(farmer_invalid_date_mask, 'Invalid Farmer Date', 'None')

    # 3. FEATURE ENGINEERING: Harvest Gap
    # Calculate days. If either date is NaT, result is NaT.
    df['Days_to_Harvest'] = (df['Expected_Harvest_Date'] - df['Disbursement_Date']).dt.days
    
    # Handle Negative Gaps (Finding 1): Loans issued AFTER expected harvest
    negative_gap_mask = df['Days_to_Harvest'] < 0
    df.loc[negative_gap_mask, 'Exclusion_Reason'] = 'After Harvest'
    
    # Handle Non-Agricultural: Explicitly mark them
    non_ag_mask = df['Customer_Type'] != 'Farmer'
    df.loc[non_ag_mask, 'Exclusion_Reason'] = 'Non-Agricultural'
    
    # Final clean DataFrame (we keep all rows, but they are now properly tagged for SQL filtering)
    final_row_count = len(df)
    validation_summary["final_valid_rows"] = final_row_count
    
    return df, validation_summary