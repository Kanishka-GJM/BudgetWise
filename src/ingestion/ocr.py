import pytesseract
from PIL import Image
import re
import pandas as pd
import os

# For Windows users, point pytesseract to your Tesseract installation:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_receipt_text(image_path):
    """Extracts raw text from a receipt image using Tesseract OCR."""
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return ""
        
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return ""

def extract_warranty_info(text):
    """
    Extracts warranty date or duration mentioned in the receipt text.
    Strictly returns has_warranty=True ONLY when a specific date or duration is explicitly stated.
    """
    if not text:
        return {"has_warranty": False, "warranty_date": None, "warranty_details": None}
        
    text_lower = text.lower()
    
    # Explicit date search
    date_patterns = [
        r'(?:warranty|warrenty|guarantee|valid\s+till|valid\s+until|exp(?:iry)?\s+date|expires?)[\s:]*([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})',
        r'(?:warranty|warrenty|guarantee|valid\s+till|valid\s+until|exp(?:iry)?\s+date|expires?)[\s:]*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})',
        r'([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})',
        r'([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})'
    ]
    
    has_warranty_kw = any(kw in text_lower for kw in ['warranty', 'warrenty', 'guarantee', 'valid till', 'valid until'])
    duration_match = re.search(r'(?:warranty|warrenty|guarantee)?[\s:]*(\d+)\s*(year|yr|month|mth)s?\s*(?:warranty|warrenty|guarantee)?', text_lower)
    
    warranty_date = None
    warranty_details = None
    
    if has_warranty_kw or duration_match:
        for pat in date_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                warranty_date = match.group(1)
                warranty_details = f"Warranty Date: {warranty_date}"
                break
                
        if not warranty_date and duration_match:
            num = int(duration_match.group(1))
            unit = duration_match.group(2)
            
            from datetime import datetime, timedelta
            today = datetime.now()
            if 'year' in unit or 'yr' in unit:
                expiry = today.replace(year=today.year + num)
            else:
                expiry = today + timedelta(days=num*30)
                
            warranty_date = expiry.strftime('%Y-%m-%d')
            warranty_details = f"{num} {'Year' if num==1 else 'Years'} Warranty (Expires: {warranty_date})"
            
    # STRICT RULE: Only set has_warranty to True if an explicit date was found
    is_valid_warranty = (warranty_date is not None)
    
    return {
        "has_warranty": is_valid_warranty,
        "warranty_date": warranty_date if is_valid_warranty else None,
        "warranty_details": warranty_details if is_valid_warranty else None
    }

def infer_bill_category_and_total(text, items):
    """Infers bill category and calculates total line-item amount."""
    text_lower = (text or "").lower()
    
    # Check items sum
    total_amount = sum(item['price'] for item in items) if items else 0.0
    
    category = "Shopping"
    if any(kw in text_lower for kw in ['mart', 'supermarket', 'grocery', 'food', 'milk', 'bread', 'eggs', 'restauran', 'cafe', 'swiggy', 'zomato']):
        category = "Food"
    elif any(kw in text_lower for kw in ['pharma', 'clinic', 'hospital', 'medici', 'doctor', 'health']):
        category = "Medical"
    elif any(kw in text_lower for kw in ['fuel', 'petrol', 'diesel', 'shell', 'hp', 'iocl']):
        category = "Fuel"
    elif any(kw in text_lower for kw in ['uber', 'ola', 'flight', 'airline', 'irctc', 'train', 'travel']):
        category = "Travel"
    elif any(kw in text_lower for kw in ['netflix', 'spotify', 'prime', 'subscription']):
        category = "Subscriptions"
        
    return category, total_amount

def parse_receipt_items(text):
    """Parses line items and prices from receipt text."""
    items = []
    price_pattern = re.compile(r'(.+?)[\s\$₹]+(\d+\.\d{2})$')
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        match = price_pattern.search(line)
        if match:
            item_name = match.group(1).strip()
            stop_words = ['total', 'tax', 'cash', 'change', 'visa', 'mastercard', 'subtotal']
            if not any(stop in item_name.lower() for stop in stop_words):
                price = float(match.group(2))
                items.append({'item': item_name, 'price': price})
                
    return items

def match_receipt_to_transaction(receipt_items, df_transactions, tolerance=0.10):
    """Attempts to find a bank transaction matching the receipt sum."""
    if not receipt_items:
        return pd.DataFrame()
        
    receipt_total = sum(item['price'] for item in receipt_items)
    df_debits = df_transactions[df_transactions['type'] == 'DEBIT']
    matches = df_debits[
        (df_debits['amount'] >= receipt_total - tolerance) & 
        (df_debits['amount'] <= receipt_total + tolerance)
    ]
    return matches
