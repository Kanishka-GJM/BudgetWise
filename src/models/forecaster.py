import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

class SpendForecaster(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

def prepare_sequence_data(series, seq_length=4):
    X, y = [], []
    for i in range(len(series) - seq_length):
        X.append(series[i:i+seq_length])
        y.append(series[i+seq_length])
    return np.array(X), np.array(y)

def train_and_forecast(df, output_path):
    print("Training Spend Forecaster...")
    # Aggregate spending by week
    df = df[df['type'] == 'DEBIT'].copy()
    df.set_index('date', inplace=True)
    weekly_spend = df.resample('W')['amount'].sum().fillna(0).values
    
    if len(weekly_spend) < 10:
        print("Not enough data to train forecaster.")
        return None
        
    scaler = MinMaxScaler()
    scaled_spend = scaler.fit_transform(weekly_spend.reshape(-1, 1))
    
    seq_length = 4
    X, y = prepare_sequence_data(scaled_spend, seq_length)
    
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32)
    
    model = SpendForecaster()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    for epoch in range(50):
        model.train()
        optimizer.zero_grad()
        preds = model(X_t)
        loss = criterion(preds, y_t)
        loss.backward()
        optimizer.step()
        
    # Forecast next week
    model.eval()
    last_seq = torch.tensor([scaled_spend[-seq_length:]], dtype=torch.float32)
    with torch.no_grad():
        pred_scaled = model(last_seq)
        
    forecast = scaler.inverse_transform(pred_scaled.numpy())[0][0]
    print(f"Forecasted next week spend: {forecast:.2f}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.save({'model_state': model.state_dict(), 'scaler': scaler}, output_path)
    return forecast
