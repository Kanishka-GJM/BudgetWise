import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
import os

class CharDataset(Dataset):
    def __init__(self, texts, labels, chars, max_len, category_map):
        self.texts = texts
        self.labels = labels
        self.char2idx = {ch: i+1 for i, ch in enumerate(chars)}
        self.max_len = max_len
        self.category_map = category_map
        
    def __len__(self):
        return len(self.texts)
        
    def __getitem__(self, idx):
        text = str(self.texts.iloc[idx])
        label = self.category_map[self.labels.iloc[idx]]
        
        # Encode
        encoded = [self.char2idx.get(c, 0) for c in text[:self.max_len]]
        # Pad
        encoded = encoded + [0] * (self.max_len - len(encoded))
        
        return torch.tensor(encoded, dtype=torch.long), torch.tensor(label, dtype=torch.long)

class TransformerClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_heads, hidden_dim, num_layers, output_dim, max_len):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.pos_encoder = nn.Embedding(max_len, embed_dim)
        
        encoder_layers = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads, dim_feedforward=hidden_dim, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.fc = nn.Linear(embed_dim, output_dim)
        
    def forward(self, x):
        seq_len = x.size(1)
        positions = torch.arange(0, seq_len, device=x.device).unsqueeze(0).expand(x.size(0), seq_len)
        embedded = self.embedding(x) + self.pos_encoder(positions)
        
        # padding mask: True where padded
        src_key_padding_mask = (x == 0)
        
        output = self.transformer_encoder(embedded, src_key_padding_mask=src_key_padding_mask)
        
        # Mean pooling ignoring padding
        mask = (x != 0).unsqueeze(-1).float()
        pooled = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        
        out = self.fc(pooled)
        return out

def train_classifier(df, model_path):
    print("Training Transformer Merchant Classifier...")
    chars = set(''.join(df['narration'].astype(str).tolist()))
    max_len = 50
    categories = df['true_category'].unique()
    category_map = {cat: i for i, cat in enumerate(categories)}
    
    dataset = CharDataset(df['narration'], df['true_category'], chars, max_len, category_map)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    model = TransformerClassifier(len(chars) + 1, embed_dim=64, num_heads=4, hidden_dim=128, num_layers=2, output_dim=len(categories), max_len=max_len)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    for epoch in range(3):
        model.train()
        total_loss = 0
        for texts, labels in loader:
            optimizer.zero_grad()
            preds = model(texts)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}, Loss: {total_loss/len(loader):.4f}")
        
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    torch.save({
        'model_state': model.state_dict(),
        'char2idx': dataset.char2idx,
        'category_map': category_map,
        'categories': categories,
        'max_len': max_len
    }, model_path)
    print(f"Model saved to {model_path}")
    return model

def predict_categories(df, model_path):
    checkpoint = torch.load(model_path, weights_only=False)
    char2idx = checkpoint['char2idx']
    category_map = checkpoint['category_map']
    categories = checkpoint['categories']
    max_len = checkpoint['max_len']
    idx2cat = {i: cat for cat, i in category_map.items()}
    
    model = TransformerClassifier(len(char2idx) + 1, embed_dim=64, num_heads=4, hidden_dim=128, num_layers=2, output_dim=len(categories), max_len=max_len)
    model.load_state_dict(checkpoint['model_state'])
    model.eval()
    
    preds_list = []
    conf_list = []
    
    for text in df['narration'].astype(str):
        encoded = [char2idx.get(c, 0) for c in text[:max_len]]
        encoded = encoded + [0] * (max_len - len(encoded))
        tensor = torch.tensor([encoded], dtype=torch.long)
        
        with torch.no_grad():
            out = model(tensor)
            probs = torch.softmax(out, dim=1)
            conf, pred = torch.max(probs, dim=1)
            
            if conf.item() < 0.4:
                preds_list.append('Uncategorized')
            else:
                preds_list.append(idx2cat[pred.item()])
            conf_list.append(conf.item())
            
    df['predicted_category'] = preds_list
    df['confidence'] = conf_list
    return df
