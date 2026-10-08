import pandas as pd
import numpy as np
import os

def clean_data(input_path, output_path):
    print(f"Cleaning data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Drop missing amounts
    initial_len = len(df)
    df = df.dropna(subset=['amount'])
    print(f"Dropped {initial_len - len(df)} records with missing amounts.")
    
    # Parse dates to ISO format
    df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True)
    
    # Sort by date for duplicate detection
    df = df.sort_values(by=['date'])
    
    # Drop exact duplicates within 60 seconds (same narration, amount, type, account)
    # We can do this by using a rolling window or grouping by a timekey.
    # A simple proxy: drop if shifted row is within 60s and has same attributes.
    df['prev_date'] = df.groupby(['narration', 'amount', 'type', 'account'])['date'].shift(1)
    df['time_diff'] = (df['date'] - df['prev_date']).dt.total_seconds()
    
    duplicates = df[(df['time_diff'] >= 0) & (df['time_diff'] <= 60)]
    df = df.drop(duplicates.index)
    print(f"Dropped {len(duplicates)} duplicate records within 60 seconds.")
    
    df = df.drop(columns=['prev_date', 'time_diff'])
    
    # Standardize schema
    df = df[['transaction_id', 'date', 'narration', 'amount', 'type', 'account', 'true_category']]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Saved cleaned data to {output_path}")
    return df
