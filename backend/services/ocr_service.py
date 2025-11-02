import re
from datetime import datetime
import pytesseract
from PIL import Image
import os

class OCRService:
    """Service for extracting text and structured data from bill images using OCR"""
    
    def __init__(self):
        # Try to use tesseract if available, otherwise use a mock implementation
        self.use_ocr = self._check_tesseract_available()
    
    def _check_tesseract_available(self):
        """Check if tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    def extract_from_image(self, image_path):
        """
        Extract bill data from an image file
        Returns a dictionary with shop_name, date, total_amount, and line_items
        """
        if not self.use_ocr:
            # Mock implementation for development/demo purposes
            return self._mock_extract(image_path)
        
        try:
            # Load and process image
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            
            # Parse extracted text
            return self._parse_bill_text(text)
        except Exception as e:
            # Fallback to mock if OCR fails
            print(f"OCR failed: {str(e)}, using mock data")
            return self._mock_extract(image_path)
    
    def _parse_bill_text(self, text):
        """Parse OCR text to extract structured bill data"""
        lines = text.split('\n')
        
        # Extract shop name (usually first line or contains common shop keywords)
        shop_name = "Unknown Shop"
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 3:
                # Check for common shop indicators
                if any(keyword in line.lower() for keyword in ['store', 'shop', 'mart', 'market', 'supermarket']):
                    shop_name = line
                    break
                elif len(shop_name.split()) == 1 or shop_name == "Unknown Shop":
                    shop_name = line
        
        # Extract date (look for date patterns)
        date = datetime.now().date()
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
        for line in lines:
            match = re.search(date_pattern, line)
            if match:
                try:
                    day, month, year = match.groups()
                    if len(year) == 2:
                        year = '20' + year
                    date = datetime(int(year), int(month), int(day)).date()
                    break
                except:
                    pass
        
        # Extract total amount (look for patterns like "Total: $XX.XX")
        total_amount = 0.0
        total_pattern = r'(?:total|amount|sum)[:\s]*\$?\s*(\d+\.?\d*)'
        for line in lines:
            match = re.search(total_pattern, line, re.IGNORECASE)
            if match:
                try:
                    total_amount = float(match.group(1))
                    break
                except:
                    pass
        
        # Extract line items (items with prices)
        line_items = []
        price_pattern = r'(\d+\.?\d*)\s*\$?'
        item_pattern = r'^(.+?)\s+(?:\d+\s+)?\$?\s*(\d+\.?\d*)$'
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Try to match item with price pattern
            match = re.match(item_pattern, line, re.IGNORECASE)
            if match:
                item_name = match.group(1).strip()
                price = float(match.group(2))
                
                # Extract quantity if present
                quantity_match = re.search(r'(\d+)\s+x\s+', line, re.IGNORECASE)
                quantity = float(quantity_match.group(1)) if quantity_match else 1.0
                
                # Determine category (simple keyword matching)
                category = self._categorize_item(item_name)
                
                line_items.append({
                    'name': item_name,
                    'quantity': quantity,
                    'price': price,
                    'category': category
                })
        
        # If no line items found but total is available, create a summary item
        if not line_items and total_amount > 0:
            line_items.append({
                'name': 'Total Purchase',
                'quantity': 1,
                'price': total_amount,
                'category': 'Uncategorized'
            })
        
        return {
            'shop_name': shop_name,
            'date': date,
            'total_amount': total_amount,
            'line_items': line_items
        }
    
    def _categorize_item(self, item_name):
        """Categorize item based on name"""
        name_lower = item_name.lower()
        
        categories = {
            'Groceries': ['milk', 'bread', 'egg', 'cheese', 'butter', 'yogurt', 'cream'],
            'Fruits & Vegetables': ['apple', 'banana', 'orange', 'tomato', 'potato', 'onion', 'carrot', 'fruit', 'vegetable'],
            'Meat & Seafood': ['chicken', 'beef', 'pork', 'fish', 'meat', 'seafood'],
            'Beverages': ['juice', 'soda', 'water', 'drink', 'coffee', 'tea', 'beer', 'wine'],
            'Snacks': ['chips', 'candy', 'cookies', 'snack', 'chocolate'],
            'Household': ['soap', 'shampoo', 'detergent', 'tissue', 'paper', 'cleaner'],
            'Personal Care': ['toothpaste', 'brush', 'deodorant', 'cream', 'lotion']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'Uncategorized'
    
    def _mock_extract(self, image_path):
        """Mock extraction for development/demo when OCR is not available"""
        filename = os.path.basename(image_path)
        
        return {
            'shop_name': 'Sample Store',
            'date': datetime.now().date(),
            'total_amount': 45.67,
            'line_items': [
                {'name': 'Milk 2L', 'quantity': 1, 'price': 3.99, 'category': 'Groceries'},
                {'name': 'Bread', 'quantity': 2, 'price': 2.50, 'category': 'Groceries'},
                {'name': 'Eggs Dozen', 'quantity': 1, 'price': 4.99, 'category': 'Groceries'},
                {'name': 'Apple', 'quantity': 1.5, 'price': 5.99, 'category': 'Fruits & Vegetables'},
                {'name': 'Orange Juice', 'quantity': 2, 'price': 7.50, 'category': 'Beverages'},
                {'name': 'Toilet Paper', 'quantity': 1, 'price': 9.99, 'category': 'Household'},
                {'name': 'Shampoo', 'quantity': 1, 'price': 6.75, 'category': 'Personal Care'},
                {'name': 'Snacks Mix', 'quantity': 3, 'price': 3.96, 'category': 'Snacks'}
            ]
        }

