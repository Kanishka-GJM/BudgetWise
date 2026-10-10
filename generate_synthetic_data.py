import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import json
import uuid
from PIL import Image, ImageDraw, ImageFont

UNIFIED_MERCHANTS = [
    # Shopping (Electronics/Retail with Warranty)
    {
        "category": "Shopping",
        "merchant": "TECH STORE ELECTRONICS",
        "items": [
            {"item": "SONY HEADPHONES", "price": 1499.00},
            {"item": "TYPE-C FAST CABLE", "price": 299.00}
        ],
        "has_warranty": True,
        "warranty_date": "2027-10-10",
        "warranty_details": "1 Year Warranty (Expires: 2027-10-10)"
    },
    {
        "category": "Shopping",
        "merchant": "VIJAY SALES ELECTRONICS",
        "items": [
            {"item": "SMART FITNESS WATCH", "price": 3499.00},
            {"item": "TEMPERED GLASS GUARD", "price": 250.00}
        ],
        "has_warranty": True,
        "warranty_date": "2027-08-15",
        "warranty_details": "1 Year Manufacturer Guarantee (Expires: 2027-08-15)"
    },
    {
        "category": "Shopping",
        "merchant": "CROMA RETAIL STORE",
        "items": [
            {"item": "BLUETOOTH SOUNDBAR", "price": 4999.00},
            {"item": "HDMI 2.1 CABLE", "price": 500.00}
        ],
        "has_warranty": True,
        "warranty_date": "2028-01-01",
        "warranty_details": "2 Year Product Warranty (Expires: 2028-01-01)"
    },
    {
        "category": "Shopping",
        "merchant": "AMAZON RETAIL INDIA",
        "items": [
            {"item": "WIRELESS ERGONOMIC MOUSE", "price": 1299.00},
            {"item": "LAPTOP SLEEVE CASE", "price": 450.00}
        ],
        "has_warranty": True,
        "warranty_date": "2027-05-20",
        "warranty_details": "1 Year Warranty (Expires: 2027-05-20)"
    },

    # Food & Dining (No Warranty)
    {
        "category": "Food",
        "merchant": "RELIANCE FRESH SUPERMART",
        "items": [
            {"item": "ORGANIC WHOLE MILK 1L", "price": 75.00},
            {"item": "MULTIGRAIN BREAD", "price": 50.00},
            {"item": "FARM FRESH EGGS 12PK", "price": 120.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Food",
        "merchant": "SWIGGY FOOD DELIVERY",
        "items": [
            {"item": "CHICKEN BIRYANI BOWL", "price": 380.00},
            {"item": "BUTTER NAAN 2X", "price": 90.00},
            {"item": "DELIVERY & TAXES", "price": 50.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Food",
        "merchant": "STARBUCKS COFFEE",
        "items": [
            {"item": "JAVACHIP FRAPPUCCINO", "price": 425.00},
            {"item": "BUTTER CROISSANT", "price": 225.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Food",
        "merchant": "ZOMATO RESTAURANT DINING",
        "items": [
            {"item": "PANEER TIKKA PLATTER", "price": 350.00},
            {"item": "MANGO LASSI 2X", "price": 160.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },

    # Healthcare & Medical (No Warranty)
    {
        "category": "Medical",
        "merchant": "APOLLO PHARMACY",
        "items": [
            {"item": "PARACETAMOL 650MG 10 TAB", "price": 45.00},
            {"item": "VITAMIN C ZINC EFFERVESCENT", "price": 220.00},
            {"item": "FIRST AID BANDAGE ROLL", "price": 85.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Medical",
        "merchant": "MAX HEALTHCARE HOSPITAL",
        "items": [
            {"item": "DOCTOR CONSULTATION FEE", "price": 800.00},
            {"item": "BLOOD TEST PANEL", "price": 1200.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },

    # Fuel & Gas (No Warranty)
    {
        "category": "Fuel",
        "merchant": "INDIAN OIL PETROL PUMP",
        "items": [
            {"item": "UNLEADED PETROL 25.0L", "price": 2500.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Fuel",
        "merchant": "BHARAT PETROLEUM HPCL",
        "items": [
            {"item": "SPEED DIESEL 30.0L", "price": 2700.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },

    # Travel & Transportation (No Warranty)
    {
        "category": "Travel",
        "merchant": "INDIGO AIRLINES",
        "items": [
            {"item": "FLIGHT TICKET MUM-DEL", "price": 4850.00},
            {"item": "WINDOW SELECTION FEE", "price": 350.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Travel",
        "merchant": "UBER INDIA RIDES",
        "items": [
            {"item": "UBER AUTO TRIP FARE", "price": 240.00},
            {"item": "TOLL CHARGES", "price": 45.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },

    # Subscriptions & Recurring Membership
    {
        "category": "Subscriptions",
        "merchant": "NETFLIX DIGITAL INDIA",
        "items": [
            {"item": "PREMIUM 4K MONTHLY SUBSCRIPTION", "price": 649.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Subscriptions",
        "merchant": "SPOTIFY MUSIC SUBSCRIPTION",
        "items": [
            {"item": "INDIVIDUAL PREMIUM MONTHLY SUBSCRIPTION", "price": 119.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Subscriptions",
        "merchant": "GOLD GYM MEMBERSHIP",
        "items": [
            {"item": "MONTHLY FITNESS GYM MEMBERSHIP", "price": 1999.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },

    # Miscellaneous (Utilities, Hardware, Legal, Donations)
    {
        "category": "Miscellaneous",
        "merchant": "ACE HARDWARE STORE",
        "items": [
            {"item": "LED BULB 12W 2X", "price": 320.00},
            {"item": "SCREWDRIVER TOOLKIT", "price": 450.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Miscellaneous",
        "merchant": "BANK CHARGES ANNUAL FEE",
        "items": [
            {"item": "ANNUAL DEBIT CARD MAINTENANCE", "price": 299.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },

    # Unknown (Unrecognized / Ambiguous transactions)
    {
        "category": "Unknown",
        "merchant": "UNKNOWN POS TRANSFER 99",
        "items": [
            {"item": "UNIDENTIFIED DEBIT CHARGE", "price": 450.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    },
    {
        "category": "Unknown",
        "merchant": "AMBIGUOUS VENDOR X7",
        "items": [
            {"item": "MISC VENDOR PAYMENT", "price": 890.00}
        ],
        "has_warranty": False,
        "warranty_date": None,
        "warranty_details": None
    }
]

def generate_bill_image(merchant_name, date_str, items, total_amount, has_warranty, warranty_date, output_path):
    """Generates a realistic receipt PNG image using PIL."""
    img = Image.new('RGB', (420, 520), color='#ffffff')
    draw = ImageDraw.Draw(img)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 20)
        font_body = ImageFont.truetype("arial.ttf", 15)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
    except:
        font_header = font_body = font_bold = ImageFont.load_default()
        
    y = 20
    draw.text((30, y), merchant_name, fill='#1e293b', font=font_header)
    y += 28
    draw.text((30, y), f"DATE: {date_str}   INV #{random.randint(100000, 999999)}", fill='#64748b', font=font_body)
    y += 25
    draw.line([(30, y), (390, y)], fill='#cbd5e1', width=2)
    y += 15
    
    for item in items:
        name = item['item']
        price_str = f"INR {item['price']:.2f}"
        draw.text((30, y), name, fill='#334155', font=font_body)
        draw.text((280, y), price_str, fill='#0f172a', font=font_body)
        y += 24
        
    y += 10
    draw.line([(30, y), (390, y)], fill='#cbd5e1', width=2)
    y += 15
    
    draw.text((30, y), "TOTAL AMOUNT:", fill='#0f172a', font=font_bold)
    draw.text((270, y), f"INR {total_amount:.2f}", fill='#10b981', font=font_bold)
    y += 35
    
    if has_warranty and warranty_date:
        draw.line([(30, y), (390, y)], fill='#f59e0b', width=1)
        y += 10
        draw.text((30, y), f"WARRANTY UNTIL: {warranty_date}", fill='#d97706', font=font_bold)
        y += 20
        draw.text((30, y), "1 YEAR GUARANTEE INCLUDED", fill='#b45309', font=font_body)
        y += 25
    else:
        draw.text((30, y), "THANK YOU FOR YOUR PURCHASE!", fill='#94a3b8', font=font_body)
        y += 25
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)

def generate_unified_dataset(num_records=500):
    print("Generating Unified Matching Dataset (Transactions + Bills)...")
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/uploads', exist_ok=True)
    
    tx_rows = []
    bills_db = {}
    
    start_date = datetime.now() - timedelta(days=90)
    
    for i in range(num_records):
        template = random.choice(UNIFIED_MERCHANTS)
        tx_id = str(uuid.uuid4())
        
        tx_date = start_date + timedelta(days=random.randint(0, 90), hours=random.randint(8, 20), minutes=random.randint(0, 59))
        date_str = tx_date.strftime('%Y-%m-%d %H:%M:%S')
        
        category = template['category']
        merchant = template['merchant']
        items = template['items']
        total_amount = sum(item['price'] for item in items)
        
        has_warranty = template['has_warranty']
        warranty_date = template['warranty_date']
        warranty_details = template['warranty_details']
        
        tx_type = 'DEBIT'
        account = random.choice(['HDFC_SAVINGS', 'ICICI_CREDIT', 'SBI_SALARY'])
        tx_rows.append([tx_id, date_str, merchant, total_amount, tx_type, account, category])
        
        # Create matching bills for first 60 records
        if i < 60:
            bill_filename = f"bill_{tx_id}.png"
            bill_img_path = os.path.join('data/uploads', bill_filename)
            
            generate_bill_image(
                merchant_name=merchant,
                date_str=date_str[:10],
                items=items,
                total_amount=total_amount,
                has_warranty=has_warranty,
                warranty_date=warranty_date,
                output_path=bill_img_path
            )
            
            bills_db[tx_id] = {
                "tx_id": tx_id,
                "filename": bill_filename,
                "image_url": f"/uploads/{bill_filename}",
                "items": items,
                "inferred_category": category,
                "bill_total": total_amount,
                "has_warranty": has_warranty,
                "warranty_date": warranty_date,
                "warranty_details": warranty_details,
                "raw_text": f"{merchant}\n" + "\n".join([f"{it['item']} {it['price']:.2f}" for it in items]) + f"\nTOTAL {total_amount:.2f}" + (f"\nWARRANTY UNTIL: {warranty_date}" if has_warranty else "")
            }
            
    # Add Income records
    for _ in range(50):
        tx_id = str(uuid.uuid4())
        tx_date = start_date + timedelta(days=random.randint(0, 90), hours=10)
        date_str = tx_date.strftime('%Y-%m-%d %H:%M:%S')
        amount = round(random.uniform(30000, 85000), 2)
        tx_rows.append([tx_id, date_str, "SALARY CREDIT - TECH CORP", amount, 'CREDIT', 'HDFC_SAVINGS', 'Income'])
        
    df = pd.DataFrame(tx_rows, columns=['transaction_id', 'date', 'narration', 'amount', 'type', 'account', 'true_category'])
    
    df.to_csv('data/raw/transactions.csv', index=False)
    print(f"Saved {len(df)} matching transactions to data/raw/transactions.csv")
    
    with open('data/attached_bills.json', 'w', encoding='utf-8') as f:
        json.dump(bills_db, f, indent=2)
    print(f"Saved {len(bills_db)} matching bill images and metadata to data/attached_bills.json")

def generate_transactions(num_records=500):
    generate_unified_dataset(num_records)

if __name__ == "__main__":
    generate_unified_dataset()
