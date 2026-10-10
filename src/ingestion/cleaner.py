import pandas as pd
import numpy as np
import os

def clean_data(input_path, output_path):
    print(f"Cleaning data from {input_path}...")
    
    if os.path.exists(input_path):
        df = pd.read_csv(input_path)
        df = df.dropna(subset=['amount'])
        df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True)
        df = df[['transaction_id', 'date', 'narration', 'amount', 'type', 'account', 'true_category']]
    elif os.path.exists('data/raw/real_transactions.parquet'):
        df = pd.read_parquet('data/raw/real_transactions.parquet')
        df = df.dropna(subset=['amount'])
        df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True)
        df = df[['transaction_id', 'date', 'narration', 'amount', 'type', 'account', 'true_category']]
    else:
        raise FileNotFoundError(f"Input file not found at {input_path}")
        
    df = df.sort_values(by=['date']).reset_index(drop=True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Saved cleaned unified matching dataset ({len(df)} records) to {output_path}")
    return df
