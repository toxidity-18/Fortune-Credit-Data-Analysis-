import pandas as pd

def load_and_clean_data(filepath: str) -> tuple[pd.DataFrame, dict]:
    """
    Loads, validates, and cleans the raw loan dataset.
    Centralizes data processing to ensure consistency across scripts.
    
    Returns a tuple: (cleaned_dataframe, exclusion_counts_dict)
    """
    # 1. Load Data
    df = pd.read_csv(filepath)
    
    # Initialize exclusion counts dictionary to expose dropped/quarantined rows
    exclusion_counts = {
        "missing_loan_id": 0,
        "duplicate_loan_id": 0,
        "invalid_amount": 0
    }

    # 2. STRICT VALIDATION & QUARANTINE
    required_cols = ['Loan_ID', 'Customer_Type', 'Loan_Amount', 'Disbursement_Date', 'Expected_Harvest_Date', 'Repayment_Status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    # --- FIX FOR FINDING 2: STRICT ID VALIDATION ---
    initial_row_count = len(df)
    
    # 1. Drop rows where Loan_ID is missing or blank
    df = df.dropna(subset=['Loan_ID'])
    exclusion_counts["missing_loan_id"] = initial_row_count - len(df)

    # 2. Drop exact duplicate Loan_IDs (keep the first occurrence)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['Loan_ID'], keep='first')
    exclusion_counts["duplicate_loan_id"] = before_dedup - len(df)

    # --- FIX FOR FINDING 5: SAFE AMOUNT PARSING ---
    # The reviewer noted that "KES 1,000" causes a TypeError. 
    # We must strip text and convert to numeric BEFORE checking for negatives.
    
    # Create a temporary clean column by removing "KES", commas, spaces, etc.
    df['Loan_Amount_Clean'] = df['Loan_Amount'].astype(str).str.replace(r'[^\d.]', '', regex=True)
    
    # Convert to numeric. Invalid strings become NaN (Not a Number).
    df['Loan_Amount_Numeric'] = pd.to_numeric(df['Loan_Amount_Clean'], errors='coerce')
    
    # Identify invalid amounts (NaN after conversion, or negative numbers)
    invalid_amount_mask = df['Loan_Amount_Numeric'].isna() | (df['Loan_Amount_Numeric'] < 0)
    exclusion_counts["invalid_amount"] = invalid_amount_mask.sum()
    
    # Calculate median ONLY from valid, non-negative amounts
    valid_amounts = df.loc[~invalid_amount_mask, 'Loan_Amount_Numeric']
    median_loan = valid_amounts.median() if not valid_amounts.empty else 0.0
    
    # Flag imputed rows and apply imputation
    df['Imputed_Loan_Amount'] = invalid_amount_mask | df['Loan_Amount'].isna()
    df['Loan_Amount'] = df['Loan_Amount_Numeric'].fillna(median_loan)
    df.loc[invalid_amount_mask, 'Loan_Amount'] = median_loan
    
    # Drop the temporary helper columns to keep the final dataframe clean
    df = df.drop(columns=['Loan_Amount_Clean', 'Loan_Amount_Numeric'])

    # 3. Data Cleaning (Status & Dates - keeping existing logic for now)
    # Standardize text
    df['Repayment_Status'] = df['Repayment_Status'].replace('repayed', 'Repaid')
    
    # Convert dates, coercing errors to NaT (Not a Time)
    df['Disbursement_Date'] = pd.to_datetime(df['Disbursement_Date'], errors='coerce')
    df['Expected_Harvest_Date'] = pd.to_datetime(df['Expected_Harvest_Date'], errors='coerce')
    
    # 4. Feature Engineering: Keep Days_to_Harvest NUMERIC
    # If Expected_Harvest_Date is NaT (e.g., for Boda Riders), this calculation naturally results in NaN.
    df['Days_to_Harvest'] = (df['Expected_Harvest_Date'] - df['Disbursement_Date']).dt.days
    
    # Flag negative harvest gaps (loan given after expected harvest)
    df['Negative_Harvest_Gap'] = df['Days_to_Harvest'] < 0
    
    return df, exclusion_counts