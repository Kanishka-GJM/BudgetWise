import os
from src.ingestion.cleaner import clean_data
from src.models.classifier import train_classifier, predict_categories
from src.models.forecaster import train_and_forecast
from src.models.anomaly import detect_anomalies

def run_pipeline():
    print("Starting BudgetWise Pipeline...")
    
    raw_path = 'data/raw/transactions.csv'
    silver_path = 'data/processed/clean_transactions.parquet'
    gold_path = 'data/gold/enriched_transactions.parquet'
    
    model_dir = 'src/models/saved'
    classifier_path = f'{model_dir}/classifier.pth'
    forecaster_path = f'{model_dir}/forecaster.pth'
    anomaly_path = f'{model_dir}/anomaly.pth'
    
    if not os.path.exists(raw_path):
        print(f"Raw data not found at {raw_path}. Run generate_synthetic_data.py first.")
        return
        
    # Bronze -> Silver
    df = clean_data(raw_path, silver_path)
    
    # Train/Predict Categories
    train_classifier(df, classifier_path)
    df = predict_categories(df, classifier_path)
    
    # Train Forecaster
    forecast = train_and_forecast(df, forecaster_path)
    
    # Anomaly Detection
    df = detect_anomalies(df, anomaly_path)
    
    # Silver -> Gold
    os.makedirs(os.path.dirname(gold_path), exist_ok=True)
    df.to_parquet(gold_path, index=False)
    print(f"Saved Gold data to {gold_path}")
    
    return forecast
