import pandas as pd
import warnings

def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    Loads, validates, and cleans the raw loan dataset.
    Centralizes data processing to ensure consistency across scripts.
    """
    # 1. Load Data
    df = pd.read_csv(filepath)
    
    # 2. Validation Checks
    required_cols = ['Loan_ID', 'Customer_Type', 'Loan_Amount', 'Disbursement_Date', 'Expected_Harvest_Date', 'Repayment_Status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    if df['Loan_ID'].duplicated().any():
        warnings.warn("Warning: Duplicate Loan_IDs detected in the dataset.")
        
    if (df['Loan_Amount'] < 0).any():
        warnings.warn("Warning: Negative Loan_Amount values detected.")
        
    valid_statuses = ['Repaid', 'Defaulted', 'Late', 'repayed']
    invalid_statuses = df[~df['Repayment_Status'].isin(valid_statuses)]['Repayment_Status'].unique()
    if len(invalid_statuses) > 0:
        warnings.warn(f"Warning: Unexpected Repayment_Status values found: {invalid_statuses}")

    # 3. Data Cleaning
    # Standardize text
    df['Repayment_Status'] = df['Repayment_Status'].replace('repayed', 'Repaid')
    
    # Flag and impute missing loan amounts (Addresses Review Point 6)
    df['Imputed_Loan_Amount'] = df['Loan_Amount'].isna()
    median_loan = df['Loan_Amount'].median()
    df['Loan_Amount'] = df['Loan_Amount'].fillna(median_loan)
    
    # Convert dates, coercing errors to NaT (Not a Time)
    df['Disbursement_Date'] = pd.to_datetime(df['Disbursement_Date'], errors='coerce')
    df['Expected_Harvest_Date'] = pd.to_datetime(df['Expected_Harvest_Date'], errors='coerce')
    
    # 4. Feature Engineering: Keep Days_to_Harvest NUMERIC (Addresses Review Point 1)
    # If Expected_Harvest_Date is NaT (e.g., for Boda Riders), this calculation naturally results in NaN.
    # NaN translates to NULL in SQLite, allowing us to filter it out cleanly in SQL.
    df['Days_to_Harvest'] = (df['Expected_Harvest_Date'] - df['Disbursement_Date']).dt.days
    
    # Optional: Flag negative harvest gaps (loan given after expected harvest)
    df['Negative_Harvest_Gap'] = df['Days_to_Harvest'] < 0
    
    return df