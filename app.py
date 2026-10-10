from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import shutil
import os
import json
from src.ingestion.ocr import extract_receipt_text, parse_receipt_items, extract_warranty_info, infer_bill_category_and_total

app = FastAPI(title="BudgetWise Web App")

# Mount uploads directory to serve bill images directly to the frontend
os.makedirs("data/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

BILLS_DB_PATH = "data/attached_bills.json"

def load_attached_bills():
    if os.path.exists(BILLS_DB_PATH):
        try:
            with open(BILLS_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_attached_bills(bills_dict):
    os.makedirs("data", exist_ok=True)
    with open(BILLS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(bills_dict, f, indent=2)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the generated HTML report as the main frontend."""
    html_path = "data/gold/report.html"
    if not os.path.exists(html_path):
        return HTMLResponse("<h1>Dashboard not found. Run `python main.py --report` first.</h1>", status_code=404)
        
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    return HTMLResponse(content=html_content)

@app.get("/api/attached-bills")
async def get_attached_bills():
    """Returns all attached bills and warranty data."""
    bills = load_attached_bills()
    return JSONResponse(bills)

@app.post("/api/upload-receipt/{tx_id}")
async def upload_receipt(tx_id: str, file: UploadFile = File(...)):
    """Accepts a receipt image, performs OCR, matches category & amount, and extracts warranty info strictly."""
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    safe_filename = f"bill_{tx_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Run Tesseract OCR
        raw_text = extract_receipt_text(file_path)
        items = parse_receipt_items(raw_text)
        warranty_info = extract_warranty_info(raw_text)
        
        # Match bill category and total amount
        inferred_category, bill_total = infer_bill_category_and_total(raw_text, items)
        
        image_url = f"/uploads/{safe_filename}"
        
        bills = load_attached_bills()
        bill_record = {
            "tx_id": tx_id,
            "filename": safe_filename,
            "image_url": image_url,
            "items": items,
            "inferred_category": inferred_category,
            "bill_total": bill_total,
            "has_warranty": warranty_info.get("has_warranty", False) if warranty_info else False,
            "warranty_date": warranty_info.get("warranty_date") if warranty_info else None,
            "warranty_details": warranty_info.get("warranty_details") if warranty_info else None,
            "raw_text": raw_text
        }
        bills[tx_id] = bill_record
        save_attached_bills(bills)
        
        return JSONResponse({
            "status": "success",
            "transaction_id": tx_id,
            "image_url": image_url,
            "items": items,
            "inferred_category": inferred_category,
            "bill_total": bill_total,
            "warranty_info": warranty_info
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    print("Starting FastAPI BudgetWise Server at http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
