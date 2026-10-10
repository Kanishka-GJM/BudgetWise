import pandas as pd
import json
import os

def identify_recurring(df):
    df_debit = df[df['type'] == 'DEBIT'].copy()
    df_debit['month_year'] = df_debit['date'].dt.to_period('M')
    recurring = df_debit.groupby('narration').agg(
        total_count=('month_year', 'count'),
        unique_months=('month_year', 'nunique')
    ).reset_index()
    
    recurring_merchants = recurring[
        (recurring['unique_months'] >= 2) & 
        (recurring['total_count'] >= recurring['unique_months'])
    ]['narration'].tolist()
    return recurring_merchants

def generate_report(forecast=None):
    gold_path = 'data/gold/enriched_transactions.parquet'
    if not os.path.exists(gold_path):
        print(f"Gold data not found at {gold_path}.")
        return
        
    df = pd.read_parquet(gold_path)
    
    # Identify subscriptions
    recurring_merchants = identify_recurring(df)
    df.loc[df['narration'].isin(recurring_merchants), 'predicted_category'] = 'Subscriptions'
    
    # Force some 'Unknown' transactions for demonstration purposes if none exist
    # (By mapping Uncategorized to Unknown)
    df['predicted_category'] = df['predicted_category'].replace('Uncategorized', 'Unknown')
    
    if len(df[df['predicted_category'] == 'Unknown']) == 0:
        # Manually set a few as Unknown to demonstrate drag and drop
        unknown_indices = df[df['type'] == 'DEBIT'].sample(min(10, len(df))).index
        df.loc[unknown_indices, 'predicted_category'] = 'Unknown'
    
    # Basic Metrics
    total_income = float(df[df['type'] == 'CREDIT']['amount'].sum())
    total_spend = float(df[df['type'] == 'DEBIT']['amount'].sum())
    savings_rate = float(((total_income - total_spend) / total_income * 100)) if total_income > 0 else 0.0
    
    # Anomalies
    anomalies = df[df['is_anomaly'] == True].head(5).to_dict(orient='records')
    
    # Process transactions for the drag-and-drop board (Debits only)
    debits = df[df['type'] == 'DEBIT'].copy()
    
    # For performance on frontend, we'll just send the top 100 recent transactions
    debits = debits.sort_values(by='date', ascending=False).head(100)
    
    # Format dates as strings
    debits['date'] = debits['date'].astype(str)
    
    # We want columns for Food, Fuel, Shopping, Medical, Travel, Subscriptions, Miscellaneous, Unknown
    categories = ['Food', 'Fuel', 'Shopping', 'Medical', 'Travel', 'Subscriptions', 'Miscellaneous', 'Unknown']
    
    # Map any odd categories to Miscellaneous to keep board clean
    debits['display_category'] = debits['predicted_category'].apply(lambda x: x if x in categories else 'Miscellaneous')
    
    # Group by category
    board_data = {cat: [] for cat in categories}
    for _, row in debits.iterrows():
        cat = row['display_category']
        board_data[cat].append({
            'id': str(row['transaction_id']),
            'date': row['date'],
            'narration': row['narration'],
            'amount': float(row['amount']),
            'anomaly': bool(row['is_anomaly'])
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --surface-color: rgba(30, 41, 59, 0.7);
            --primary: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
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
            margin-bottom: 3rem;
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
            margin-bottom: 3rem;
        }}
        
        .metric-card {{
            background: var(--surface-color);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
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
            padding-bottom: 1rem;
            align-items: flex-start;
        }}
        
        .column {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 1rem;
            min-width: 300px;
            max-width: 300px;
            display: flex;
            flex-direction: column;
            max-height: 70vh;
        }}
        
        .column-header {{
            padding: 1rem;
            font-weight: 600;
            border-bottom: 1px solid rgba(255,255,255,0.05);
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
        
        .badge {{
            background: rgba(255,255,255,0.1);
            padding: 0.25rem 0.5rem;
            border-radius: 1rem;
            font-size: 0.75rem;
        }}
        
        .column-body {{
            padding: 1rem;
            overflow-y: auto;
            flex: 1;
            min-height: 150px;
        }}
        
        .tx-card {{
            background: var(--surface-color);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 0.75rem;
            cursor: grab;
            transition: all 0.2s;
        }}
        
        .tx-card:active {{ cursor: grabbing; }}
        
        .tx-card.dragging {{
            opacity: 0.5;
            transform: scale(0.95);
        }}
        
        .tx-top {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }}
        
        .tx-narration {{
            font-weight: 600;
            font-size: 0.9rem;
            word-break: break-all;
        }}
        
        .tx-amount {{
            font-weight: 700;
            color: #f8fafc;
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
            margin-top: 0.5rem;
            border: 1px solid rgba(239, 68, 68, 0.4);
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
        <p style="color: var(--text-muted)">Intelligent categorization and insights</p>
    </header>
    
    <div class="metrics-grid" id="metrics-container">
        <!-- Metrics injected by JS -->
    </div>
    
    <div style="background: var(--surface-color); padding: 1.5rem; border-radius: 1rem; margin-bottom: 3rem; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);">
        <h2 style="margin-bottom: 1rem; font-size: 1.2rem;">Spending Breakdown</h2>
        <div style="height: 300px; display: flex; justify-content: center;">
            <canvas id="categoryChart"></canvas>
        </div>
    </div>
    
    <h2 style="margin-bottom: 1rem; font-size: 1.2rem;">Transaction Categorizer</h2>
    <p style="color: var(--text-muted); margin-bottom: 2rem; font-size: 0.9rem;">
        Drag and drop transactions from the <strong style="color:var(--warning)">Unknown</strong> column into their correct categories to update your spending profile.
    </p>

    <div class="board" id="board-container">
        <!-- Columns injected by JS -->
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
        
        // Render Board
        const board = document.getElementById('board-container');
        
        // Calculate initial chart data from board data
        const initialChartData = appData.categories.map(cat => {{
            const txs = appData.board[cat] || [];
            return txs.reduce((sum, tx) => sum + tx.amount, 0);
        }});

        // Render Chart
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

        appData.categories.forEach(cat => {{
            const txs = appData.board[cat] || [];
            const colHtml = `
                <div class="column col-${{cat}}" data-category="${{cat}}">
                    <div class="column-header">
                        <span>${{cat}}</span>
                        <span class="badge" id="badge-${{cat}}">${{txs.length}}</span>
                    </div>
                    <div class="column-body" id="col-${{cat}}">
                        ${{txs.map(tx => `
                            <div class="tx-card" draggable="true" id="${{tx.id}}" data-amount="${{tx.amount}}">
                                <div class="tx-top">
                                    <div class="tx-narration">${{tx.narration}}</div>
                                    <div class="tx-amount">${{formatMoney(tx.amount)}}</div>
                                </div>
                                <div class="tx-date">${{tx.date.substring(0, 16)}}</div>
                                ${{tx.anomaly ? `<div class="anomaly-badge">Anomaly Detected</div>` : ''}}
                            </div>
                        `).join('')}}
                    </div>
                </div>
            `;
            board.innerHTML += colHtml;
        }});
        
        // Drag and Drop Logic
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
                badge.innerText = container.children.length;
                
                // Recalculate amounts for chart
                let sum = 0;
                for(let i=0; i<container.children.length; i++) {{
                    sum += parseFloat(container.children[i].getAttribute('data-amount'));
                }}
                newChartData.push(sum);
            }});
            
            if (window.myChart) {{
                window.myChart.data.datasets[0].data = newChartData;
                window.myChart.update();
            }}
        }}
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
