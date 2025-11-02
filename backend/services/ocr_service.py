import re
from datetime import datetime
import pytesseract
from PIL import Image
import os

# Try to import OpenCV for image preprocessing
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Try to import EasyOCR, fallback to Tesseract only if not available
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

class OCRService:
    """Service for extracting text and structured data from bill images using OCR"""
    
    def __init__(self):
        # Try EasyOCR first (better accuracy), then Tesseract, then mock
        self.use_easyocr = self._check_easyocr_available()
        self.use_tesseract = self._check_tesseract_available()
        self.use_ocr = self.use_easyocr or self.use_tesseract
        
        # Initialize EasyOCR reader if available
        if self.use_easyocr:
            try:
                print("Initializing EasyOCR...")
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
                print("EasyOCR initialized successfully")
            except Exception as e:
                print(f"EasyOCR initialization failed: {e}, falling back to Tesseract")
                self.use_easyocr = False
    
    def _check_easyocr_available(self):
        """Check if EasyOCR is available"""
        return EASYOCR_AVAILABLE
    
    def _check_tesseract_available(self):
        """Check if tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    def _preprocess_image(self, image_path):
        """Preprocess image for better OCR accuracy"""
        if not CV2_AVAILABLE:
            return None
        
        try:
            # Read image with OpenCV
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return binary
        except Exception as e:
            print(f"Image preprocessing failed: {e}")
            return None
    
    def extract_from_image(self, image_path):
        """
        Extract bill data from an image file
        Returns data in CSV format structure: Date, Shop Address, Item Name, Quantity, Cost per unit, Total amount paid, Item Type, Item Sub Type
        """
        if not self.use_ocr:
            # Mock implementation for development/demo when OCR is not available
            return self._mock_extract(image_path)
        
        text = ""
        try:
            # Preprocess image for better OCR
            preprocessed_img = self._preprocess_image(image_path)
            
            # Try EasyOCR first (better accuracy for receipts)
            if self.use_easyocr and hasattr(self, 'easyocr_reader'):
                try:
                    print("Using EasyOCR for text extraction...")
                    # Use preprocessed image if available, otherwise original
                    if preprocessed_img is not None:
                        results = self.easyocr_reader.readtext(preprocessed_img)
                    else:
                        results = self.easyocr_reader.readtext(image_path)
                    
                    # Combine all detected text
                    text_lines = []
                    for (bbox, detected_text, confidence) in results:
                        if confidence > 0.3:  # Filter low confidence results
                            text_lines.append(detected_text)
                    text = '\n'.join(text_lines)
                    print(f"EasyOCR extracted {len(text_lines)} lines of text")
                except Exception as e:
                    print(f"EasyOCR failed: {e}, falling back to Tesseract")
                    text = None
            
            # Fallback to Tesseract if EasyOCR failed or not available
            if not text or len(text.strip()) < 20:
                print("Using Tesseract for text extraction...")
                image = Image.open(image_path)
                
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Try OCR with different configurations
                if preprocessed_img is not None:
                    # Convert OpenCV image to PIL Image for Tesseract
                    pil_image = Image.fromarray(preprocessed_img)
                    text = pytesseract.image_to_string(pil_image, config='--psm 6')
                else:
                    text = pytesseract.image_to_string(image, config='--psm 6')
                
                # If text is too short, try different page segmentation mode
                if len(text.strip()) < 50:
                    text = pytesseract.image_to_string(image, config='--psm 3')
            
            if not text or len(text.strip()) < 10:
                print("OCR extracted insufficient text, using mock data")
                return self._mock_extract(image_path)
            
            print(f"Extracted text length: {len(text)} characters")
            
            # Parse extracted text into CSV-like structure
            parsed_data = self._parse_bill_text_to_csv_format(text)
            
            # If parsing didn't extract much, try alternative patterns
            if not parsed_data.get('line_items') or len(parsed_data.get('line_items', [])) < 2:
                print("Trying enhanced parsing...")
                parsed_data = self._parse_bill_text_enhanced_to_csv_format(text, image_path)
            
            return parsed_data
        except Exception as e:
            # Fallback to mock if OCR fails
            print(f"OCR failed: {str(e)}, using mock data")
            return self._mock_extract(image_path)
    
    def _parse_bill_text_to_csv_format(self, text):
        """
        Parse OCR text and return data in CSV format structure:
        Returns dict with: Date, Shop Address, and list of items with:
        Item Name, Quantity, Cost per unit, Total amount paid, Item Type, Item Sub Type
        """
        lines = text.split('\n')
        
        # Extract shop name (Shop Address)
        shop_name = "Unknown Shop"
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) > 3:
                # Check for common shop indicators
                if any(keyword in line.lower() for keyword in ['store', 'shop', 'mart', 'market', 'supermarket', 'retail', 'grocery', 'costco', 'walmart', 'target', 'safeway', 'kroger']):
                    shop_name = line
                    break
                elif shop_name == "Unknown Shop" and len(line) > 5 and not any(skip in line.lower() for skip in ['date', 'time', 'invoice', 'receipt']):
                    shop_name = line
        
        # Extract date
        date = datetime.now().date()
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
            r'(\w{3,9})\s+(\d{1,2}),\s+(\d{4})',  # Month DD, YYYY
        ]
        
        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        parts = match.groups()
                        if len(parts) == 3:
                            if '/' in line or '-' in line:
                                if len(parts[0]) == 4:  # YYYY-MM-DD
                                    year, month, day = parts
                                    date = datetime(int(year), int(month), int(day)).date()
                                else:  # MM-DD-YYYY or DD-MM-YYYY
                                    part1, part2, year_part = parts
                                    if int(part1) > 12:  # DD-MM-YYYY
                                        day, month, year = part1, part2, year_part
                                    else:  # MM-DD-YYYY
                                        month, day, year = part1, part2, year_part
                                    if len(year) == 2:
                                        year = '20' + year
                                    date = datetime(int(year), int(month), int(day)).date()
                                break
                    except:
                        continue
            if date != datetime.now().date():
                break
        
        # Extract total amount (check last 10 lines)
        total_amount = 0.0
        total_patterns = [
            r'(?:total|grand\s+total|amount\s+due|balance)[:\s]*\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:\.\d{2})?)',
            r'\$\s*(\d{1,3}(?:[.,]\d{3})*(?:\.\d{2})?)\s*(?:total|due|amount)?',
        ]
        
        for line in lines[-10:]:
            for pattern in total_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        total_amount = float(amount_str)
                        break
                    except:
                        pass
            if total_amount > 0:
                break
        
        # Extract line items - CSV format: Item Name, Quantity, Cost per unit, Total amount paid, Item Type, Item Sub Type
        line_items = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip header/footer/common lines
            skip_keywords = ['item', 'description', 'qty', 'quantity', 'price', 'total', 'subtotal', 
                           'tax', 'receipt', 'invoice', 'date', 'time', 'cashier', 'register',
                           'password', 'pin', 'card', 'signature', 'thank', 'visit', 'change',
                           'cash', 'tendered', 'balance', 'discount', 'coupon', 'voucher',
                           'refund', 'return', 'exchange', 'void', 'cancelled', 'transaction']
            if any(skip in line.lower() for skip in skip_keywords):
                continue
            
            # Skip lines that look like passwords or PINs
            if re.match(r'^\d+(\.\d+)?[xX]\s*\$?\s*\d+', line):
                continue
            
            # Skip purely numeric lines
            if re.match(r'^\s*\$?\s*\d{1,2}(?:[.,]\d{3})*(?:\.\d{2})?\s*$', line):
                continue
            
            # Patterns to match line items with prices
            patterns = [
                r'^(.+?)\s+\$?\s*(\d+\.?\d{2})\s*$',  # Item $price
                r'^(.+?)\s+x?\s*(\d+(?:\.\d+)?)\s+\$?(\d+\.?\d{2})$',  # Item x2 $price
                r'^(.+?)\s+(\d+\.?\d{2})\s*\$?\s*$',  # Item price
                r'^(.+?)\s+(\d+)\s+x\s+\$?(\d+\.?\d{2})$',  # Item 2 x $price
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        groups = match.groups()
                        item_name = groups[0].strip()
                        
                        # Skip if item name looks invalid
                        if (item_name.replace('.', '').replace(',', '').isdigit() or 
                            re.match(r'^\d{1,2}[/-]', item_name) or
                            len(item_name) < 2):
                            continue
                        
                        # Extract quantity and price
                        quantity = 1.0
                        item_price = 0.0  # Cost per unit
                        item_total = 0.0  # Total amount paid
                        
                        if len(groups) == 3:  # Has quantity and price
                            try:
                                quantity = float(groups[1])
                                price_str = groups[2].replace(',', '')
                                item_price = float(price_str)
                                item_total = item_price * quantity
                            except:
                                continue
                        elif len(groups) == 2:  # Just price (quantity = 1)
                            try:
                                val_str = groups[1].replace(',', '')
                                if '.' in val_str:
                                    item_price = float(val_str)
                                    item_total = item_price
                                else:
                                    continue
                            except:
                                continue
                        
                        # Validate price is reasonable
                        if item_price <= 0 or item_price >= 1000 or item_total >= 1000:
                            continue
                        
                        # Categorize item
                        category = self._categorize_item(item_name)
                        item_type = category  # Item Type = category
                        item_sub_type = 'NA'  # Item Sub Type (can be enhanced later)
                        
                        # Add to line items in CSV format
                        line_items.append({
                            'Item Name': item_name,
                            'Quantity': quantity,
                            'Cost per unit': item_price,
                            'Total amount paid': item_total,
                            'Item Type': item_type,
                            'Item Sub Type': item_sub_type
                        })
                        break
                    except Exception as e:
                        continue
        
        # Calculate total from items if we have line items
        if line_items and total_amount == 0:
            total_amount = sum(item['Total amount paid'] for item in line_items)
        
        return {
            'Date': date.isoformat(),
            'Shop Address': shop_name,
            'line_items': line_items,
            'total_amount': total_amount
        }
    
    def _parse_bill_text_enhanced_to_csv_format(self, text, image_path=None):
        """Enhanced parsing with more flexible patterns, returns CSV format"""
        lines = text.split('\n')
        
        shop_name = "Unknown Shop"
        for line in lines[:15]:
            line = line.strip()
            if line and len(line) > 3:
                if any(skip in line.lower() for skip in ['date', 'time', 'invoice', 'receipt', 'total', 'subtotal']):
                    continue
                if any(keyword in line.lower() for keyword in ['store', 'shop', 'mart', 'market', 'supermarket', 'retail', 'grocery']):
                    shop_name = line
                    break
                elif shop_name == "Unknown Shop" and len(line) > 5:
                    shop_name = line
        
        date = datetime.now().date()
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(\w{3,9})\s+(\d{1,2}),\s+(\d{4})',
        ]
        
        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and len(match.groups()) == 3:
                    try:
                        parts = match.groups()
                        if '/' in line or '-' in line:
                            if len(parts[0]) == 4:
                                year, month, day = parts
                                date = datetime(int(year), int(month), int(day)).date()
                            else:
                                part1, part2, year_part = parts
                                if int(part1) > 12:
                                    day, month, year = part1, part2, year_part
                                else:
                                    month, day, year = part1, part2, year_part
                                if len(year) == 2:
                                    year = '20' + year
                                date = datetime(int(year), int(month), int(day)).date()
                            break
                    except:
                        continue
            if date != datetime.now().date():
                break
        
        total_amount = 0.0
        total_patterns = [
            r'(?:total|grand\s+total|amount\s+due|balance)[:\s]*\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:\.\d{2})?)',
            r'\$\s*(\d{1,3}(?:[.,]\d{3})*(?:\.\d{2})?)\s*(?:total|due|amount)?',
        ]
        
        for line in lines[-10:]:
            for pattern in total_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        total_amount = float(amount_str)
                        break
                    except:
                        pass
            if total_amount > 0:
                break
        
        line_items = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            skip_keywords = ['item', 'description', 'qty', 'quantity', 'price', 'total', 'subtotal', 
                           'tax', 'receipt', 'invoice', 'date', 'time', 'password', 'pin', 'card',
                           'signature', 'thank', 'visit', 'change', 'cash', 'tendered', 'balance']
            if any(skip in line.lower() for skip in skip_keywords):
                continue
            
            if re.match(r'^\d+(\.\d+)?[xX]\s*\$?\s*\d+', line):
                continue
            
            if re.match(r'^\s*\$?\s*\d{1,2}(?:[.,]\d{3})*(?:\.\d{2})?\s*$', line):
                continue
            
            patterns = [
                r'^(.+?)\s+\$?\s*(\d+\.?\d{2})\s*$',
                r'^(.+?)\s+x?\s*(\d+)\s+\$?(\d+\.?\d{2})$',
                r'^(.+?)\s+(\d+\.?\d{2})\s*\$?\s*$',
                r'^(.+?)\s+(\d+)\s+x\s+\$?(\d+\.?\d{2})$',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        groups = match.groups()
                        item_name = groups[0].strip()
                        
                        if (item_name.replace('.', '').replace(',', '').isdigit() or 
                            re.match(r'^\d{1,2}[/-]', item_name) or len(item_name) < 2):
                            continue
                        
                        quantity = 1.0
                        item_price = 0.0
                        item_total = 0.0
                        
                        if len(groups) == 3:
                            try:
                                quantity = float(groups[1])
                                price_str = groups[2].replace(',', '')
                                item_price = float(price_str)
                                item_total = item_price * quantity
                            except:
                                continue
                        elif len(groups) == 2:
                            try:
                                val_str = groups[1].replace(',', '')
                                if '.' in val_str:
                                    item_price = float(val_str)
                                    item_total = item_price
                                else:
                                    continue
                            except:
                                continue
                        
                        if item_price <= 0 or item_price >= 1000 or item_total >= 1000:
                            continue
                        
                        category = self._categorize_item(item_name)
                        
                        line_items.append({
                            'Item Name': item_name,
                            'Quantity': quantity,
                            'Cost per unit': item_price,
                            'Total amount paid': item_total,
                            'Item Type': category,
                            'Item Sub Type': 'NA'
                        })
                        break
                    except:
                        continue
        
        if line_items and total_amount == 0:
            total_amount = sum(item['Total amount paid'] for item in line_items)
        
        return {
            'Date': date.isoformat(),
            'Shop Address': shop_name,
            'line_items': line_items,
            'total_amount': total_amount
        }
    
    def _categorize_item(self, item_name):
        """Categorize item based on name"""
        if not item_name or len(item_name.strip()) < 2:
            return 'Uncategorized'
        
        name_lower = item_name.lower().strip()
        
        # Skip if item name looks like a price, date, or password
        if (name_lower.replace('.', '').replace(',', '').isdigit() or
            re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', name_lower) or
            re.match(r'^\d+(\.\d+)?[xX]', name_lower) or
            'password' in name_lower or 'pin' in name_lower):
            return 'Uncategorized'
        
        # More comprehensive categorization with priority order
        categories = {
            'Dairy': [
                'organic a2', 'a2 milk', 'half & half', 'greek yogurt', 'sour cream', 'cottage cheese',
                'whole milk', 'skim milk', 'almond milk', 'soy milk', 'oat milk', 'coconut milk',
                'milk', 'cheese', 'butter', 'yogurt', 'cream', 'dairy', 'mozzarella', 'cheddar',
                'parmesan', 'swiss', 'feta', 'cream cheese', 'ricotta'
            ],
            'Grain': [
                'whole wheat', 'white bread', 'wheat bread', 'sourdough', 'multigrain',
                'bread', 'wheat', 'grain', 'flour', 'rice', 'pasta', 'noodle', 'quinoa',
                'oats', 'cereal', 'bagel', 'tortilla', 'naan', 'roti', 'pita', 'wraps',
                'buns', 'rolls', 'basmati', 'jasmine rice', 'brown rice', 'white rice'
            ],
            'Fruit': [
                'strawberry', 'blueberry', 'raspberry', 'blackberry', 'cranberry',
                'pineapple', 'mango', 'avocado', 'grapefruit', 'watermelon', 'cantaloupe',
                'apple', 'banana', 'orange', 'berry', 'grape', 'fruit', 'fruits',
                'citrus', 'peach', 'pear', 'plum', 'kiwi', 'lemon', 'lime', 'cherry'
            ],
            'Vegetable': [
                'bell pepper', 'green pepper', 'red pepper', 'broccoli', 'cauliflower', 'cucumber',
                'lettuce', 'spinach', 'tomato', 'potato', 'onion', 'carrot', 'pepper',
                'vegetable', 'vegetables', 'veggie', 'veggies', 'garlic', 'ginger', 'celery',
                'corn', 'peas', 'beans', 'cabbage', 'zucchini', 'squash', 'eggplant',
                'mushroom', 'asparagus', 'brussels sprouts'
            ],
            'Meat & Seafood': [
                'ground beef', 'ground turkey', 'ground chicken', 'chicken breast', 'chicken thighs',
                'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'tilapia', 'cod', 'halibut',
                'chicken', 'beef', 'pork', 'fish', 'meat', 'seafood', 'turkey', 'lamb',
                'bacon', 'sausage', 'ham', 'hot dog', 'burger', 'steak', 'ribs'
            ],
            'Herb': [
                'cilantro', 'coriander', 'basil', 'parsley', 'rosemary', 'thyme', 'mint',
                'oregano', 'sage', 'dill', 'herb', 'herbs', 'chives', 'tarragon'
            ],
            'Daal': [
                'toor dal', 'moong dal', 'chana dal', 'masoor dal', 'urad dal',
                'daal', 'dal', 'lentil', 'lentils', 'pulse', 'legume'
            ],
            'Paste': [
                'toothpaste', 'tomato paste', 'garlic paste', 'ginger paste', 'curry paste',
                'paste', 'tooth', 'dental'
            ],
            'Pooja item': [
                'pooja', 'puja', 'incense', 'diya', 'camphor', 'kumkum', 'agarbatti', 'dhoop'
            ],
            'Snacks': [
                'potato chips', 'tortilla chips', 'corn chips', 'pretzel', 'trail mix', 'granola',
                'chips', 'candy', 'cookies', 'snack', 'snacks', 'chocolate', 'crackers',
                'nuts', 'almond', 'walnut', 'peanut', 'cashew', 'pistachio'
            ],
            'Syrup': [
                'maple syrup', 'chocolate syrup', 'caramel syrup',
                'syrup', 'honey', 'molasses', 'agave', 'jam', 'jelly', 'preserve'
            ],
            'Body soap': [
                'body soap', 'hand soap', 'bar soap', 'body wash', 'shower gel', 'liquid soap',
                'soap', 'bath', 'cleanser'
            ],
            'Household': [
                'dish soap', 'laundry detergent', 'dishwasher detergent', 'trash bag', 'ziploc',
                'detergent', 'tissue', 'paper', 'cleaner', 'disinfectant', 'bleach',
                'foil', 'wrap', 'sponge', 'brush', 'towel', 'napkin', 'toilet paper'
            ],
            'Beverages': [
                'orange juice', 'apple juice', 'cranberry juice', 'iced tea', 'green tea',
                'juice', 'soda', 'water', 'drink', 'coffee', 'tea', 'beer', 'wine',
                'beverage', 'lemonade', 'smoothie', 'energy drink', 'sports drink'
            ],
            'Personal Care': [
                'hair shampoo', 'body lotion', 'face wash', 'face moisturizer',
                'shampoo', 'conditioner', 'deodorant', 'lotion', 'moisturizer', 'sunscreen',
                'razor', 'toothbrush', 'floss', 'mouthwash', 'toner', 'serum', 'cream'
            ]
        }
        
        # Try matching from longest to shortest keywords for better specificity
        for category, keywords in categories.items():
            sorted_keywords = sorted(keywords, key=len, reverse=True)
            for keyword in sorted_keywords:
                if ' ' in keyword:
                    if keyword in name_lower:
                        return category
                else:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, name_lower):
                        return category
        
        return 'Uncategorized'
    
    def _mock_extract(self, image_path):
        """Mock extraction for development/demo when OCR is not available"""
        filename = os.path.basename(image_path)
        date = datetime.now().date()
        
        # Return in CSV format structure
        return {
            'Date': date.isoformat(),
            'Shop Address': 'Sample Store',
            'line_items': [
                {
                    'Item Name': 'Milk 2L',
                    'Quantity': 1.0,
                    'Cost per unit': 3.99,
                    'Total amount paid': 3.99,
                    'Item Type': 'Dairy',
                    'Item Sub Type': 'NA'
                },
                {
                    'Item Name': 'Bread',
                    'Quantity': 2.0,
                    'Cost per unit': 2.50,
                    'Total amount paid': 5.00,
                    'Item Type': 'Grain',
                    'Item Sub Type': 'NA'
                },
                {
                    'Item Name': 'Apple',
                    'Quantity': 1.5,
                    'Cost per unit': 3.99,
                    'Total amount paid': 5.99,
                    'Item Type': 'Fruit',
                    'Item Sub Type': 'NA'
                }
            ],
            'total_amount': 14.98
        }
