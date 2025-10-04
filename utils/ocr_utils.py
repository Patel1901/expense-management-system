import pytesseract
from PIL import Image
import re
from datetime import datetime

def extract_receipt_data(image_path):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        
        extracted_data = {
            'amount': extract_amount(text),
            'date': extract_date(text),
            'vendor': extract_vendor(text),
            'description': text[:200] if text else '',
            'raw_text': text
        }
        
        return extracted_data
    except Exception as e:
        print(f"OCR Error: {e}")
        return None

def extract_amount(text):
    patterns = [
        r'(?:total|amount|sum)[:\s]*[\$\£\€]?\s*(\d+(?:\.\d{2})?)',
        r'[\$\£\€]\s*(\d+(?:\.\d{2})?)',
        r'(\d+\.\d{2})\s*(?:total|amount)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    return None

def extract_date(text):
    patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d %B %Y', '%d %b %Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
    return None

def extract_vendor(text):
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 3 and not re.match(r'^\d', line):
            return line[:100]
    return None
