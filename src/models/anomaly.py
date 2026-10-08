import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler

class AnomalyAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 4)
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

def detect_anomalies(df, model_path):
    print("Training Anomaly Autoencoder...")
    # Features: amount, hour, day of week
    features = df[['amount']].copy()
    features['hour'] = df['date'].dt.hour
    features['dayofweek'] = df['date'].dt.dayofweek
    
    # Fill any remaining NaNs
    features = features.fillna(0)
    
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    X_t = torch.tensor(scaled_features, dtype=torch.float32)
    
    model = AnomalyAutoencoder(input_dim=3)
    criterion = nn.MSELoss(reduction='none')
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    dataset = torch.utils.data.TensorDataset(X_t)
    loader = torch.utils.data.DataLoader(dataset, batch_size=128, shuffle=True)
    
    for epoch in range(10):
        model.train()
        for batch in loader:
            batch_x = batch[0]
            optimizer.zero_grad()
            reconstructed = model(batch_x)
            loss = criterion(reconstructed, batch_x).mean()
            loss.backward()
            optimizer.step()
            
    # Calculate reconstruction errors
    model.eval()
    with torch.no_grad():
        reconstructed = model(X_t)
        errors = torch.mean((reconstructed - X_t) ** 2, dim=1).numpy()
        
    threshold = np.percentile(errors, 95)
    df['anomaly_score'] = errors
    df['is_anomaly'] = errors > threshold
    
    print(f"Detected {df['is_anomaly'].sum()} anomalies.")
    
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    torch.save({'model_state': model.state_dict(), 'scaler': scaler}, model_path)
    
    return df
