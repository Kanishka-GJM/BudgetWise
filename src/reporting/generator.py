import pandas as pd
import json
import os
import shutil

def identify_recurring(df):
    df_debit = df[df['type'] == 'DEBIT'].copy()
    df_debit['month_year'] = df_debit['date'].dt.to_period('M')
    
    sub_keywords = ['netflix', 'spotify', 'prime', 'subscription', 'membership', 'streaming', 'gym']
    
    # Filter for narrations that contain subscription keywords
    is_sub_merchant = df_debit['narration'].str.lower().apply(lambda text: any(kw in text for kw in sub_keywords))
    df_debit = df_debit[is_sub_merchant]
    
    if len(df_debit) == 0:
        return []
        
    recurring = df_debit.groupby('narration').agg(
        total_count=('month_year', 'count'),
        unique_months=('month_year', 'nunique')
    ).reset_index()
    
    recurring_merchants = recurring[
        (recurring['unique_months'] >= 2) & 
        (recurring['total_count'] >= recurring['unique_months'])
    ]['narration'].tolist()
    return recurring_merchants

def load_or_seed_attached_bills(df_debits):
    bills_path = 'data/attached_bills.json'
    os.makedirs('data/uploads', exist_ok=True)
    
    bills = {}
    if os.path.exists(bills_path):
        try:
            with open(bills_path, 'r', encoding='utf-8') as f:
                bills = json.load(f)
        except Exception:
            bills = {}
            
    # Seed demonstration bill if none exist
    if not bills and len(df_debits) > 0:
        sample_src = 'sample_receipt.png'
        dest_filename = 'bill_sample_receipt.png'
        dest_path = os.path.join('data/uploads', dest_filename)
        
        if os.path.exists(sample_src):
            shutil.copy(sample_src, dest_path)
            
        shopping_txs = df_debits[df_debits['predicted_category'] == 'Shopping']
        target_tx_id = str(shopping_txs.iloc[0]['transaction_id']) if len(shopping_txs) > 0 else str(df_debits.iloc[0]['transaction_id'])
        
        bills[target_tx_id] = {
            "tx_id": target_tx_id,
            "filename": dest_filename,
            "image_url": f"/uploads/{dest_filename}",
            "items": [
                {"item": "HEADPHONES", "price": 1499.00},
                {"item": "TYPE-C CABLE", "price": 299.00}
            ],
            "inferred_category": "Shopping",
            "bill_total": 1798.00,
            "has_warranty": True,
            "warranty_date": "2027-10-10",
            "warranty_details": "1 Year Guarantee Included (Expires: 2027-10-10)",
            "raw_text": "TECH STORE ELECTRONICS\nHEADPHONES 1499.00\nTYPE-C CABLE 299.00\nTOTAL 1798.00\nWARRANTY UNTIL: 2027-10-10\n1 YEAR GUARANTEE INCLUDED"
        }
        
        with open(bills_path, 'w', encoding='utf-8') as f:
            json.dump(bills, f, indent=2)
            
    return bills

def generate_report(forecast=None):
    gold_path = 'data/gold/enriched_transactions.parquet'
    if not os.path.exists(gold_path):
        print(f"Gold data not found at {gold_path}.")
        return
        
    df = pd.read_parquet(gold_path)
    
    # Identify subscriptions
    recurring_merchants = identify_recurring(df)
    df.loc[df['narration'].isin(recurring_merchants), 'predicted_category'] = 'Subscriptions'
    
    df['predicted_category'] = df['predicted_category'].replace('Uncategorized', 'Unknown')
    
    # Metrics
    total_income = float(df[df['type'] == 'CREDIT']['amount'].sum())
    total_spend = float(df[df['type'] == 'DEBIT']['amount'].sum())
    savings_rate = float(((total_income - total_spend) / total_income * 100)) if total_income > 0 else 0.0
    
    debits = df[df['type'] == 'DEBIT'].copy()
    debits = debits.sort_values(by='date', ascending=False).head(100)
    debits['date'] = debits['date'].astype(str)
    
    categories = ['Food', 'Fuel', 'Shopping', 'Medical', 'Travel', 'Subscriptions', 'Miscellaneous', 'Unknown']
    debits['display_category'] = debits['predicted_category'].apply(lambda x: x if x in categories else 'Miscellaneous')
    
    attached_bills = load_or_seed_attached_bills(debits)
    
    board_data = {cat: [] for cat in categories}
    for _, row in debits.iterrows():
        cat = row['display_category']
        tx_id = str(row['transaction_id'])
        bill_info = attached_bills.get(tx_id, None)
        
        # If bill total is specified, align transaction amount with bill sum
        tx_amount = float(bill_info['bill_total']) if (bill_info and bill_info.get('bill_total', 0) > 0) else float(row['amount'])
        
        board_data[cat].append({
            'id': tx_id,
            'date': row['date'],
            'narration': row['narration'],
            'amount': tx_amount,
            'anomaly': bool(row['is_anomaly']),
            'bill': bill_info
        })
        
    dashboard_data = {
        'totalIncome': total_income,
        'totalSpend': total_spend,
        'savingsRate': savings_rate,
        'forecast': float(forecast) if forecast else 0.0,
        'board': board_data,
        'categories': categories
    }
    
    json_data = json.dumps(dashboard_data)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BudgetWise Analytics</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --surface-color: rgba(30, 41, 59, 0.7);
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-glow: rgba(255, 255, 255, 0.08);
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
        }}
        
        body {{
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.15) 0px, transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem;
            background-attachment: fixed;
        }}
        
        header {{
            margin-bottom: 2.5rem;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(to right, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        
        .metric-card {{
            background: var(--surface-color);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-glow);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-4px);
        }}
        
        .metric-title {{
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 600;
        }}
        
        .value-income {{ color: var(--success); }}
        .value-spend {{ color: var(--danger); }}
        .value-neutral {{ color: var(--primary); }}
        
        .board {{
            display: flex;
            gap: 1.5rem;
            overflow-x: auto;
            padding-bottom: 1.5rem;
            align-items: flex-start;
        }}
        
        .column {{
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid var(--border-glow);
            border-radius: 1rem;
            min-width: 310px;
            max-width: 310px;
            display: flex;
            flex-direction: column;
            max-height: 75vh;
            backdrop-filter: blur(8px);
        }}
        
        .column-header {{
            padding: 1rem;
            font-weight: 600;
            border-bottom: 1px solid var(--border-glow);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .col-Unknown .column-header {{ border-top: 3px solid var(--warning); }}
        .col-Food .column-header {{ border-top: 3px solid #f43f5e; }}
        .col-Fuel .column-header {{ border-top: 3px solid #8b5cf6; }}
        .col-Shopping .column-header {{ border-top: 3px solid #ec4899; }}
        .col-Medical .column-header {{ border-top: 3px solid #14b8a6; }}
        .col-Travel .column-header {{ border-top: 3px solid #eab308; }}
        .col-Subscriptions .column-header {{ border-top: 3px solid #3b82f6; }}
        .col-Miscellaneous .column-header {{ border-top: 3px solid #64748b; }}
        
        .header-badges {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .badge {{
            background: rgba(255,255,255,0.1);
            padding: 0.25rem 0.55rem;
            border-radius: 1rem;
            font-size: 0.75rem;
        }}

        .cat-warranty-badge {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(16, 185, 129, 0.3));
            color: #fbbf24;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.2rem 0.5rem;
            border-radius: 0.8rem;
            border: 1px solid rgba(245, 158, 11, 0.5);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}
        
        .column-body {{
            padding: 1rem;
            overflow-y: auto;
            flex: 1;
            min-height: 150px;
        }}
        
        .tx-card {{
            background: var(--surface-color);
            border: 1px solid var(--border-glow);
            border-radius: 0.75rem;
            padding: 1rem;
            margin-bottom: 0.85rem;
            cursor: grab;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .tx-card:hover {{
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.25);
        }}
        
        .tx-card:active {{ cursor: grabbing; }}
        
        .tx-card.dragging {{
            opacity: 0.4;
            transform: scale(0.96);
        }}
        
        .tx-top {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.4rem;
        }}
        
        .tx-narration {{
            font-weight: 600;
            font-size: 0.9rem;
            word-break: break-word;
        }}
        
        .tx-amount {{
            font-weight: 700;
            color: #f8fafc;
            font-size: 0.95rem;
        }}
        
        .tx-date {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}
        
        .anomaly-badge {{
            display: inline-block;
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
            font-size: 0.65rem;
            padding: 0.15rem 0.4rem;
            border-radius: 0.25rem;
            margin-top: 0.4rem;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }}

        .warranty-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(16, 185, 129, 0.2));
            color: #fef08a;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 0.4rem;
            margin-top: 0.5rem;
            border: 1px solid rgba(245, 158, 11, 0.4);
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.15);
        }}

        .bill-attachment-box {{
            margin-top: 0.75rem;
            padding-top: 0.6rem;
            border-top: 1px dashed rgba(255,255,255,0.1);
        }}

        .bill-thumb-container {{
            position: relative;
            margin-top: 0.5rem;
            border-radius: 0.5rem;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.15);
            cursor: pointer;
            height: 90px;
            background: #000;
        }}

        .bill-thumb-container img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0.85;
            transition: transform 0.3s, opacity 0.3s;
        }}

        .bill-thumb-container:hover img {{
            transform: scale(1.05);
            opacity: 1;
        }}

        .bill-thumb-overlay {{
            position: absolute;
            inset: 0;
            background: rgba(15, 23, 42, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 0.75rem;
            font-weight: 600;
            backdrop-filter: blur(2px);
            opacity: 0;
            transition: opacity 0.2s;
        }}

        .bill-thumb-container:hover .bill-thumb-overlay {{
            opacity: 1;
        }}

        .btn-view-bill {{
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 600;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-top: 6px;
            transition: background 0.2s, transform 0.1s;
        }}

        .btn-view-bill:hover {{
            background: linear-gradient(135deg, #2563eb, #1e40af);
            transform: translateY(-1px);
        }}

        .btn-attach {{
            background: rgba(255,255,255,0.08);
            color: var(--text-main);
            border: 1px solid rgba(255,255,255,0.15);
            padding: 5px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            width: 100%;
            transition: background 0.2s;
        }}

        .btn-attach:hover {{
            background: rgba(255,255,255,0.15);
        }}

        /* Modal Styles */
        .modal-backdrop {{
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            animation: fadeIn 0.2s ease-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .modal-card {{
            background: #1e293b;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 1rem;
            width: 100%;
            max-width: 900px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }}

        .modal-header {{
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(15, 23, 42, 0.5);
        }}

        .modal-close-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
        }}

        .modal-close-btn:hover {{ color: white; }}

        .modal-body {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            padding: 1.5rem;
            overflow-y: auto;
        }}

        @media (max-width: 768px) {{
            .modal-body {{ grid-template-columns: 1fr; }}
        }}

        .modal-left {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #0f172a;
            border-radius: 0.75rem;
            padding: 1rem;
            border: 1px solid rgba(255,255,255,0.05);
        }}

        .modal-bill-image {{
            max-width: 100%;
            max-height: 450px;
            object-fit: contain;
            border-radius: 0.5rem;
            box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        }}

        .modal-right {{
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        .warranty-card-alert {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(16, 185, 129, 0.15));
            border: 1px solid rgba(245, 158, 11, 0.4);
            border-radius: 0.75rem;
            padding: 1rem;
        }}

        .warranty-card-alert h4 {{
            color: #fbbf24;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 0.4rem;
            font-size: 1rem;
        }}

        .item-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.85rem;
        }}

        /* Scrollbar styles */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.2); }}
    </style>
</head>
<body>

    <header>
        <h1>BudgetWise Dashboard</h1>
        <p style="color: var(--text-muted)">Intelligent transaction categorization, OCR bill matching & strict warranty tracking</p>
    </header>
    
    <div class="metrics-grid" id="metrics-container">
        <!-- Metrics injected by JS -->
    </div>
    
    <div style="background: var(--surface-color); padding: 1.5rem; border-radius: 1rem; margin-bottom: 3rem; border: 1px solid var(--border-glow); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);">
        <h2 style="margin-bottom: 1rem; font-size: 1.2rem;">Spending Breakdown</h2>
        <div style="height: 300px; display: flex; justify-content: center;">
            <canvas id="categoryChart"></canvas>
        </div>
    </div>
    
    <h2 style="margin-bottom: 0.5rem; font-size: 1.2rem;">Transaction & Bill Categorizer</h2>
    <p style="color: var(--text-muted); margin-bottom: 2rem; font-size: 0.9rem;">
        Drag and drop transactions between categories. View attached bills (category & amount auto-aligned) and track <strong>🛡️ Warranty Dates</strong> (displayed only when explicitly specified).
    </p>

    <div class="board" id="board-container">
        <!-- Columns injected by JS -->
    </div>

    <!-- Bill Viewer Modal -->
    <div id="billModal" class="modal-backdrop" style="display:none;" onclick="closeBillModal(event)">
        <div class="modal-card" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:1.4rem;">🧾</span>
                    <h3 id="modalTxTitle">Attached Bill Details</h3>
                </div>
                <button class="modal-close-btn" onclick="closeBillModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="modal-left">
                    <img id="modalBillImg" src="" alt="Attached Bill" class="modal-bill-image">
                    <div style="margin-top:12px;">
                        <a id="modalBillOpenLink" href="#" target="_blank" style="color:var(--primary); font-size:0.8rem; text-decoration:none; font-weight:600;">↗️ Open Full Image</a>
                    </div>
                </div>
                <div class="modal-right">
                    <div id="modalWarrantyBox"></div>
                    
                    <div style="background: rgba(15,23,42,0.5); padding: 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.05);">
                        <h4 style="font-size:0.85rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:0.5rem;">Transaction Details</h4>
                        <div id="modalTxMeta" style="font-size:0.9rem; display:flex; flex-direction:column; gap:4px;"></div>
                    </div>

                    <div style="background: rgba(15,23,42,0.5); padding: 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.05); flex: 1;">
                        <h4 style="font-size:0.85rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:0.5rem;">Parsed Line Items (OCR)</h4>
                        <div id="modalItemsList"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const appData = {json_data};
        
        // Format Currency
        const formatMoney = (amount) => {{
            return new Intl.NumberFormat('en-IN', {{ style: 'currency', currency: 'INR' }}).format(amount);
        }};
        
        // Render Metrics
        document.getElementById('metrics-container').innerHTML = `
            <div class="metric-card">
                <div class="metric-title">Total Income</div>
                <div class="metric-value value-income">${{formatMoney(appData.totalIncome)}}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Total Expenditure</div>
                <div class="metric-value value-spend">${{formatMoney(appData.totalSpend)}}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Savings Rate</div>
                <div class="metric-value value-neutral">${{appData.savingsRate.toFixed(1)}}%</div>
            </div>
        `;
        
        const board = document.getElementById('board-container');
        
        const initialChartData = appData.categories.map(cat => {{
            const txs = appData.board[cat] || [];
            return txs.reduce((sum, tx) => sum + tx.amount, 0);
        }});

        const ctx = document.getElementById('categoryChart').getContext('2d');
        window.myChart = new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: appData.categories,
                datasets: [{{
                    data: initialChartData,
                    backgroundColor: [
                        '#f43f5e', '#8b5cf6', '#ec4899', '#14b8a6', 
                        '#eab308', '#3b82f6', '#64748b', '#f59e0b'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right', labels: {{ color: '#94a3b8' }} }}
                }}
            }}
        }});

        function renderBoard() {{
            board.innerHTML = '';
            appData.categories.forEach(cat => {{
                const txs = appData.board[cat] || [];
                // STRICT CONDITION: Only count warranty if explicitly specified
                const warrantyCount = txs.filter(tx => tx.bill && tx.bill.has_warranty && tx.bill.warranty_date).length;
                
                const colHtml = `
                    <div class="column col-${{cat}}" data-category="${{cat}}">
                        <div class="column-header">
                            <span>${{cat}}</span>
                            <div class="header-badges">
                                ${{warrantyCount > 0 ? `<span class="cat-warranty-badge" id="cat-warr-${{cat}}">🛡️ ${{warrantyCount}} Warranty</span>` : `<span id="cat-warr-${{cat}}"></span>`}}
                                <span class="badge" id="badge-${{cat}}">${{txs.length}}</span>
                            </div>
                        </div>
                        <div class="column-body" id="col-${{cat}}">
                            ${{txs.map(tx => renderTxCard(tx)).join('')}}
                        </div>
                    </div>
                `;
                board.innerHTML += colHtml;
            }});
            setupDragAndDrop();
        }}

        function renderTxCard(tx) {{
            const hasBill = tx.bill && tx.bill.image_url;
            // STRICT WARRANTY CONDITION: Only render warranty badge when explicitly specified
            const hasWarranty = tx.bill && tx.bill.has_warranty && tx.bill.warranty_date;
            const warrDate = hasWarranty ? tx.bill.warranty_date : '';
            
            return `
                <div class="tx-card" draggable="true" id="${{tx.id}}" data-amount="${{tx.amount}}">
                    <div class="tx-top">
                        <div class="tx-narration">${{tx.narration}}</div>
                        <div class="tx-amount">${{formatMoney(tx.amount)}}</div>
                    </div>
                    <div class="tx-date">${{tx.date.substring(0, 16)}}</div>
                    ${{tx.anomaly ? `<div class="anomaly-badge">Anomaly Detected</div>` : ''}}
                    
                    ${{hasWarranty ? `
                        <div class="warranty-badge">
                            🛡️ Warranty Exp: <strong>${{warrDate}}</strong>
                        </div>
                    ` : ''}}

                    <div class="bill-attachment-box">
                        ${{hasBill ? `
                            <div class="bill-thumb-container" onclick="openBillModal('${{tx.id}}')">
                                <img src="${{tx.bill.image_url}}" alt="Bill">
                                <div class="bill-thumb-overlay">👁️ View Bill</div>
                            </div>
                            <button class="btn-view-bill" onclick="openBillModal('${{tx.id}}')">
                                👁️ View Attached Bill
                            </button>
                        ` : `
                            <input type="file" id="file-${{tx.id}}" style="display:none;" accept="image/*" onchange="uploadReceipt('${{tx.id}}')">
                            <button class="btn-attach" onclick="document.getElementById('file-${{tx.id}}').click()">+ Attach Receipt / Bill</button>
                            <div id="receipt-results-${{tx.id}}" style="font-size: 0.75rem; margin-top: 5px;"></div>
                        `}}
                    </div>
                </div>
            `;
        }}

        function setupDragAndDrop() {{
            const draggables = document.querySelectorAll('.tx-card');
            const containers = document.querySelectorAll('.column-body');
            
            draggables.forEach(draggable => {{
                draggable.addEventListener('dragstart', () => {{
                    draggable.classList.add('dragging');
                }});
                
                draggable.addEventListener('dragend', () => {{
                    draggable.classList.remove('dragging');
                    updateCounts();
                }});
            }});
            
            containers.forEach(container => {{
                container.addEventListener('dragover', e => {{
                    e.preventDefault();
                    const afterElement = getDragAfterElement(container, e.clientY);
                    const draggable = document.querySelector('.dragging');
                    if (afterElement == null) {{
                        container.appendChild(draggable);
                    }} else {{
                        container.insertBefore(draggable, afterElement);
                    }}
                }});
            }});
        }}

        function getDragAfterElement(container, y) {{
            const draggableElements = [...container.querySelectorAll('.tx-card:not(.dragging)')];
            return draggableElements.reduce((closest, child) => {{
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;
                if (offset < 0 && offset > closest.offset) {{
                    return {{ offset: offset, element: child }}
                }} else {{
                    return closest;
                }}
            }}, {{ offset: Number.NEGATIVE_INFINITY }}).element;
        }}
        
        function updateCounts() {{
            const newChartData = [];
            appData.categories.forEach(cat => {{
                const container = document.getElementById(`col-${{cat}}`);
                const badge = document.getElementById(`badge-${{cat}}`);
                const warrBadge = document.getElementById(`cat-warr-${{cat}}`);
                badge.innerText = container.children.length;
                
                let sum = 0;
                let warrantyCount = 0;
                for(let i=0; i<container.children.length; i++) {{
                    const card = container.children[i];
                    sum += parseFloat(card.getAttribute('data-amount'));
                    if (card.querySelector('.warranty-badge')) {{
                        warrantyCount++;
                    }}
                }}
                newChartData.push(sum);
                
                if (warrBadge) {{
                    if (warrantyCount > 0) {{
                        warrBadge.className = "cat-warranty-badge";
                        warrBadge.innerText = `🛡️ ${{warrantyCount}} Warranty`;
                    }} else {{
                        warrBadge.innerText = "";
                        warrBadge.className = "";
                    }}
                }}
            }});
            
            if (window.myChart) {{
                window.myChart.data.datasets[0].data = newChartData;
                window.myChart.update();
            }}
        }}

        function openBillModal(txId) {{
            let targetTx = null;
            let currentCat = null;
            for (const cat of appData.categories) {{
                const found = (appData.board[cat] || []).find(t => t.id === txId);
                if (found) {{ targetTx = found; currentCat = cat; break; }}
            }}
            
            if (!targetTx || !targetTx.bill) return;

            const bill = targetTx.bill;
            document.getElementById('modalTxTitle').innerText = `Bill: ${{targetTx.narration}} (${{formatMoney(targetTx.amount)}})`;
            document.getElementById('modalBillImg').src = bill.image_url;
            document.getElementById('modalBillOpenLink').href = bill.image_url;

            const warrBox = document.getElementById('modalWarrantyBox');
            if (bill.has_warranty && bill.warranty_date) {{
                warrBox.innerHTML = `
                    <div class="warranty-card-alert">
                        <h4>🛡️ WARRANTY COVERAGE SPECIFIED</h4>
                        <div style="font-size:0.9rem; color:#fef08a; font-weight:600;">
                            Expiry Date: ${{bill.warranty_date}}
                        </div>
                        <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">
                            ${{bill.warranty_details || 'Verified warranty details extracted from uploaded bill.'}}
                        </div>
                    </div>
                `;
            }} else {{
                warrBox.innerHTML = `
                    <div style="background: rgba(15,23,42,0.4); padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.05); font-size:0.8rem; color:var(--text-muted);">
                        ℹ️ No warranty date specified on this bill.
                    </div>
                `;
            }}

            document.getElementById('modalTxMeta').innerHTML = `
                <div><strong>Merchant:</strong> ${{targetTx.narration}}</div>
                <div><strong>Amount:</strong> ${{formatMoney(targetTx.amount)}}</div>
                <div><strong>Category:</strong> ${{currentCat}}</div>
                <div><strong>Transaction Date:</strong> ${{targetTx.date.substring(0, 16)}}</div>
            `;

            const itemsBox = document.getElementById('modalItemsList');
            if (bill.items && bill.items.length > 0) {{
                itemsBox.innerHTML = bill.items.map(item => `
                    <div class="item-row">
                        <span>${{item.item}}</span>
                        <span style="font-weight:600;">₹${{item.price.toFixed(2)}}</span>
                    </div>
                `).join('');
            }} else {{
                itemsBox.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted); padding:0.5rem 0;">No specific line items split on this bill.</div>`;
            }}

            document.getElementById('billModal').style.display = 'flex';
        }}

        function closeBillModal(event) {{
            if (!event || event.target.id === 'billModal' || event.target.classList.contains('modal-close-btn')) {{
                document.getElementById('billModal').style.display = 'none';
            }}
        }}

        async function uploadReceipt(txId) {{
            const fileInput = document.getElementById(`file-${{txId}}`);
            if (!fileInput.files.length) return;
            
            const resultsDiv = document.getElementById(`receipt-results-${{txId}}`);
            resultsDiv.innerText = "Scanning & matching category/amount...";
            resultsDiv.style.color = "var(--warning)";
            
            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            
            try {{
                const response = await fetch(`/api/upload-receipt/${{txId}}`, {{
                    method: 'POST',
                    body: formData
                }});
                const data = await response.json();
                
                if (data.status === "success") {{
                    let foundTx = null;
                    let oldCat = null;
                    
                    for (const cat of appData.categories) {{
                        const idx = (appData.board[cat] || []).findIndex(t => t.id === txId);
                        if (idx !== -1) {{
                            foundTx = appData.board[cat].splice(idx, 1)[0];
                            oldCat = cat;
                            break;
                        }}
                    }}
                    
                    if (foundTx) {{
                        foundTx.bill = {{
                            image_url: data.image_url,
                            items: data.items,
                            has_warranty: data.warranty_info ? data.warranty_info.has_warranty : false,
                            warranty_date: data.warranty_info ? data.warranty_info.warranty_date : null,
                            warranty_details: data.warranty_info ? data.warranty_info.warranty_details : null
                        }};
                        
                        // Align category & amount
                        if (data.bill_total && data.bill_total > 0) {{
                            foundTx.amount = data.bill_total;
                        }}
                        const targetCat = (data.inferred_category && appData.categories.includes(data.inferred_category)) ? data.inferred_category : oldCat;
                        
                        appData.board[targetCat] = appData.board[targetCat] || [];
                        appData.board[targetCat].push(foundTx);
                    }}
                    
                    renderBoard();
                    updateCounts();
                }} else {{
                    resultsDiv.innerText = "Failed to process receipt.";
                    resultsDiv.style.color = "var(--danger)";
                }}
            }} catch (err) {{
                console.error(err);
                resultsDiv.innerText = "Failed to connect to server.";
                resultsDiv.style.color = "var(--danger)";
            }}
        }}

        renderBoard();
    </script>
</body>
</html>
"""
    os.makedirs('data/gold', exist_ok=True)
    with open('data/gold/report.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print("Interactive Dashboard generated at data/gold/report.html")

if __name__ == "__main__":
    generate_report()
