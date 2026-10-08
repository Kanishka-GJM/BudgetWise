# BudgetWise 💰

BudgetWise is an automated personal finance categorization and insights pipeline built on the **Medallion Architecture** (Bronze, Silver, Gold). It leverages **Deep Learning** modules to ingest raw, noisy bank and UPI transaction exports, clean them, categorize them intelligently, forecast future spending, and detect anomalies.

Finally, it produces a rich, interactive web dashboard for you to visualize your finances and manually categorize unknown transactions using a drag-and-drop kanban board.

## 🏗️ Architecture (Medallion)
* **🥉 Bronze (`data/raw/`)**: Ingestion of raw, messy, and duplicated CSV/UPI data.
* **🥈 Silver (`data/processed/`)**: Data validated, missing amounts dropped, dates parsed, and exact duplicates purged (AutoRecoverDQ). Stored efficiently as `.parquet`.
* **🥇 Gold (`data/gold/`)**: Enriched data! Machine learning predictions (categories, forecasts, anomalies) are merged and compiled into an interactive HTML dashboard.

## 🧠 Deep Learning Modules (PyTorch)
1. **BiLSTM Merchant Classifier**: A character-level Bidirectional LSTM that reads raw narrations (like `UPI-SWIGGY*BLR0123-PAY`) and assigns them to core categories (`Food`, `Shopping`, `Medical`, `Travel`, etc.). 
    - *Active Learning mechanism*: If confidence is below 70%, it assigns it to `Unknown` for human-in-the-loop review on the dashboard.
2. **LSTM Spend Forecaster**: A sequence model that looks at historical rolling multi-week aggregate spending to forecast what you'll spend next week.
3. **Autoencoder Anomaly Detector**: Extracts features like `amount`, `hour`, and `day of week`. The autoencoder reconstructs these features and flags transactions with a reconstruction error > 95th percentile as anomalies.

## 🚀 How to Run

### 1. Install Dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Run the Full Pipeline End-to-End
This will generate synthetic raw data, clean it, train the PyTorch models, run the predictions, and compile the final dashboard:
```bash
python main.py --all
```

### 3. View the Dashboard
Once the pipeline finishes, a visually appealing dashboard is created in the gold layer. You can view it by double-clicking the file or running:
```bash
Start-Process "data\gold\report.html"
```

## 📁 Repository Structure
```
budgetwise/
├── data/
│   ├── raw/             # Generated synthetic transactions
│   ├── processed/       # Cleaned parquet data
│   └── gold/            # Final dashboard & enriched data
├── src/
│   ├── ingestion/       # Cleaner and DQ logic
│   ├── models/          # PyTorch model definitions (Classifier, Forecaster, Autoencoder)
│   ├── pipeline/        # Orchestration connecting Bronze -> Silver -> Gold
│   └── reporting/       # Interactive HTML dashboard generator
├── main.py              # CLI entry point
├── generate_synthetic_data.py # Data simulator
└── requirements.txt
```