from PIL import Image, ImageDraw, ImageFont
import os
from src.ingestion.ocr import extract_receipt_text, parse_receipt_items, extract_warranty_info

def create_sample_receipt():
    img = Image.new('RGB', (350, 450), color='white')
    d = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
        
    text = """
    TECH STORE ELECTRONICS
    -----------------------------
    HEADPHONES          1499.00
    TYPE-C CABLE         299.00
    -----------------------------
    TOTAL               1798.00
    
    WARRANTY UNTIL: 2027-10-10
    1 YEAR GUARANTEE INCLUDED
    """
    
    d.text((20, 20), text, fill='black', font=font)
    img.save('sample_receipt.png')
    print("Successfully created 'sample_receipt.png' with Warranty details!")

if __name__ == "__main__":
    create_sample_receipt()
    
    print("\n--- Running Tesseract OCR ---")
    raw_text = extract_receipt_text('sample_receipt.png')
    if raw_text:
        print(f"Extracted Text:\n{raw_text}")
    else:
        print("Failed to extract text.")
        
    print("\n--- Parsing Extracted Items ---")
    items = parse_receipt_items(raw_text)
    for item in items:
        print(f"Found Item: {item['item']} - Price: ${item['price']}")
        
    print("\n--- Extracting Warranty Info ---")
    warranty_info = extract_warranty_info(raw_text)
    print(f"Warranty Extraction Result: {warranty_info}")
