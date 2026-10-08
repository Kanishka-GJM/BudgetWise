import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
from faker import Faker

fake = Faker('en_IN')

CATEGORIES = {
    'Food': ['UPI-SWIGGY', 'ZOMATO ONLINE', 'STARBUCKS', 'MCDONALDS', 'DOMINOS PIZZA'],
    'Fuel': ['INDIAN OIL', 'BHARAT PETROLEUM', 'HPCL', 'SHELL'],
    'Shopping': ['AMAZON INDIA', 'FLIPKART', 'MYNTRA', 'RELIANCE FRESH', 'DMART'],
    'Medical': ['APOLLO PHARMACY', 'MEDICAL STORE', 'CLINIC', 'HOSPITAL'],
    'Travel': ['UBER', 'OLA', 'MAKE MY TRIP', 'INDIGO', 'IRCTC'],
    'Subscriptions': ['NETFLIX', 'AMAZON PRIME', 'GYM SUBSCRIPTION', 'SPOTIFY'],
    'Miscellaneous': ['HARDWARE STORE', 'STATIONERY', 'DONATION'],
    'Income': ['SALARY*CREDIT', 'UPI*REFUND', 'INTEREST CREDIT', 'DIVIDEND']
}

def generate_transactions(num_records=5000):
    data = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(num_records):
        tx_id = fake.uuid4()
        
        # Date generation with some messy formats
        date_obj = start_date + timedelta(days=random.randint(0, 300), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        format_choice = random.random()
        if format_choice < 0.1:
            date_str = date_obj.strftime('%d-%m-%Y %H:%M')
        elif format_choice < 0.2:
            date_str = date_obj.strftime('%Y/%m/%d %H:%M:%S')
        else:
            date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            
        category = random.choice(list(CATEGORIES.keys()))
        narration = random.choice(CATEGORIES[category])
        
        # Add some noise to narration
        if random.random() < 0.1:
            narration = narration.lower()
        if random.random() < 0.05:
            narration = narration + " " + fake.word()
            
        # Amount
        if category == 'Income':
            amount = round(random.uniform(5000, 100000), 2)
            tx_type = 'CREDIT'
        else:
            amount = round(random.uniform(10, 5000), 2)
            tx_type = 'DEBIT'
            
        # Introduce missing amounts
        if random.random() < 0.02:
            amount = np.nan
            
        account = random.choice(['HDFC_SAVINGS', 'SBI_SALARY', 'ICICI_CREDIT'])
        
        data.append([tx_id, date_str, narration, amount, tx_type, account, category])
        
        # Introduce duplicates within 60 seconds
        if random.random() < 0.01:
            dup_date = date_obj + timedelta(seconds=random.randint(1, 59))
            data.append([fake.uuid4(), dup_date.strftime('%Y-%m-%d %H:%M:%S'), narration, amount, tx_type, account, category])

    df = pd.DataFrame(data, columns=['transaction_id', 'date', 'narration', 'amount', 'type', 'account', 'true_category'])
    
    # Ensure directory exists
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/transactions.csv', index=False)
    print(f"Generated {len(df)} records at data/raw/transactions.csv")

if __name__ == "__main__":
    generate_transactions()
