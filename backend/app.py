from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import csv
import io
from sqlalchemy import extract

from models import db, Bill, LineItem
from services.ocr_service import OCRService
from services.analysis_service import AnalysisService

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///bills.db')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'pdf', 'csv'}

# Initialize database
db.init_app(app)

# Create uploads and data directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
data_dir = os.environ.get('DATA_DIR', 'data')
os.makedirs(data_dir, exist_ok=True)

# Ensure database directory exists and has correct permissions
if DATABASE_URL.startswith('sqlite:///'):
    db_path = DATABASE_URL.replace('sqlite:///', '')
    if db_path and not db_path.startswith(':memory:'):
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            # Ensure directory is writable
            os.chmod(db_dir, 0o755)

# Create tables on startup
with app.app_context():
    db.create_all()

# Initialize services
ocr_service = OCRService()
analysis_service = AnalysisService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/bills/upload-image', methods=['POST'])
def upload_image():
    """Upload a bill image and extract line items using OCR"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Extract data using OCR (now returns CSV format structure)
            extracted_data = ocr_service.extract_from_image(filepath)
            
            # Parse date from ISO format string
            date_str = extracted_data.get('Date', '')
            try:
                bill_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                bill_date = datetime.now().date()
            
            shop_name = extracted_data.get('Shop Address', 'Unknown Shop')
            total_amount = extracted_data.get('total_amount', 0.0)
            
            # Get line items in CSV format
            csv_line_items = extracted_data.get('line_items', [])
            
            # Check for duplicate bill (same shop, date, and total amount)
            existing_bill = Bill.query.filter_by(
                shop_name=shop_name,
                date=bill_date,
                total_amount=total_amount
            ).first()
            
            if existing_bill:
                # Delete the uploaded file since it's a duplicate
                try:
                    os.remove(filepath)
                except:
                    pass
                
                return jsonify({
                    'success': False,
                    'message': 'Duplicate bill detected. This bill already exists.',
                    'existing_bill_id': existing_bill.id,
                    'shop_name': existing_bill.shop_name,
                    'date': existing_bill.date.isoformat(),
                    'total_amount': float(existing_bill.total_amount)
                }), 409  # 409 Conflict
            
            # Calculate total from items if not provided
            if total_amount == 0 and csv_line_items:
                total_amount = sum(item.get('Total amount paid', 0.0) for item in csv_line_items)
            
            # Create bill record
            bill = Bill(
                shop_name=shop_name,
                date=bill_date,
                total_amount=total_amount,
                upload_type='image',
                file_path=filepath
            )
            db.session.add(bill)
            db.session.flush()
            
            # Create line items from CSV format structure
            # Match CSV upload logic: prioritize Item Sub Type, then Item Type, then Uncategorized
            line_items = []
            for item in csv_line_items:
                # Get category - prioritize Item Sub Type over Item Type (same as CSV upload)
                item_type = item.get('Item Type', '').strip()
                item_sub_type = item.get('Item Sub Type', '').strip()
                category = item_sub_type if item_sub_type and item_sub_type.lower() != 'na' else item_type if item_type else 'Uncategorized'
                
                line_item = LineItem(
                    bill_id=bill.id,
                    item_name=item.get('Item Name', ''),
                    quantity=float(item.get('Quantity', 1.0)),
                    price=float(item.get('Cost per unit', 0.0)),
                    category=category
                )
                db.session.add(line_item)
                line_items.append({
                    'name': line_item.item_name,
                    'quantity': float(line_item.quantity),
                    'price': float(line_item.price),
                    'category': line_item.category
                })
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'bill_id': bill.id,
                'shop_name': bill.shop_name,
                'date': bill.date.isoformat(),
                'total_amount': float(bill.total_amount),
                'line_items': line_items
            }), 201
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to process image: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/bills/upload-csv', methods=['POST'])
def upload_csv():
    """Upload a CSV file with bill data"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Read CSV content
            file_content = file.stream.read().decode("UTF8")
            stream = io.StringIO(file_content, newline=None)
            csv_reader = csv.DictReader(stream)
            
            # Detect CSV format by checking headers
            headers = csv_reader.fieldnames or []
            is_line_item_format = 'Item Name' in headers or any('item name' in h.lower() for h in headers) if headers else False
            
            # Reset stream for reading
            stream = io.StringIO(file_content, newline=None)
            csv_reader = csv.DictReader(stream)
            
            bills_created = []
            errors = []
            
            if is_line_item_format:
                # Format: Each row is a line item with Date, Shop Address, etc.
                bills_dict = {}  # Key: (date, shop_name), Value: list of line items
                
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Skip empty rows
                        item_name = row.get('Item Name', '').strip()
                        if not item_name or item_name.lower() in ['tax', 'tax :', '']:
                            continue
                        
                        # Parse date - handle formats like "02/09/2025", "2/15/2025"
                        date_str = row.get('Date', '').strip()
                        bill_date = None
                        
                        for date_format in ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d/%m/%Y']:
                            try:
                                bill_date = datetime.strptime(date_str, date_format).date()
                                break
                            except:
                                continue
                        
                        if not bill_date:
                            continue
                        
                        # Get shop name
                        shop_name = row.get('Shop Address', '').strip() or row.get('Shop Name', '').strip()
                        if not shop_name:
                            shop_name = 'Unknown Shop'
                        
                        # Create bill key
                        bill_key = (bill_date.isoformat(), shop_name)
                        
                        # Parse item details
                        try:
                            # Get total amount paid for this item
                            total_amount_str = row.get('Total amount paid', '').strip() or row.get('Total Amount Paid', '').strip()
                            total_amount_str = total_amount_str.replace('$', '').replace(',', '').strip()
                            
                            # Get quantity
                            quantity_str = row.get('Quantity', '').strip()
                            quantity = float(quantity_str) if quantity_str and quantity_str.lower() != 'na' else 1.0
                            
                            # Get price per unit or use total amount
                            cost_per_unit_str = row.get('Cost per unit', '').strip() or row.get('Cost Per Unit', '').strip()
                            cost_per_unit_str = cost_per_unit_str.replace('$', '').replace(',', '').strip()
                            
                            if total_amount_str and total_amount_str.lower() != 'nan':
                                item_total = float(total_amount_str)
                                item_price = float(cost_per_unit_str) if cost_per_unit_str and cost_per_unit_str.lower() != 'na' else item_total / quantity if quantity > 0 else item_total
                            else:
                                continue
                            
                            # Get category
                            item_type = row.get('Item Type', '').strip() or row.get('Item type', '').strip()
                            item_sub_type = row.get('Item Sub Type', '').strip() or row.get('Item Sub Type', '').strip()
                            category = item_sub_type if item_sub_type and item_sub_type.lower() != 'na' else item_type if item_type else 'Uncategorized'
                            
                            # Add to bills_dict
                            if bill_key not in bills_dict:
                                bills_dict[bill_key] = []
                            
                            bills_dict[bill_key].append({
                                'name': item_name,
                                'quantity': quantity,
                                'price': item_price,
                                'total': item_total,
                                'category': category
                            })
                        
                        except Exception as e:
                            errors.append(f'Row {row_num}: Failed to parse item - {str(e)}')
                    
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
                
                # Create bills from grouped data
                for (date_str, shop_name), items in bills_dict.items():
                    try:
                        bill_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        total_amount = sum(item['total'] for item in items)
                        
                        # Check for duplicate bill (same shop, date, and total amount)
                        existing_bill = Bill.query.filter_by(
                            shop_name=shop_name,
                            date=bill_date,
                            total_amount=total_amount
                        ).first()
                        
                        if existing_bill:
                            # Skip this bill, it's a duplicate
                            errors.append(f'Duplicate bill skipped: {shop_name} on {bill_date.isoformat()} with total ${total_amount:.2f}')
                            continue
                        
                        # Create bill
                        bill = Bill(
                            shop_name=shop_name,
                            date=bill_date,
                            total_amount=total_amount,
                            upload_type='csv',
                            file_path=None
                        )
                        db.session.add(bill)
                        db.session.flush()
                        
                        # Create line items
                        for item in items:
                            line_item = LineItem(
                                bill_id=bill.id,
                                item_name=item['name'],
                                quantity=item['quantity'],
                                price=item['price'],
                                category=item['category']
                            )
                            db.session.add(line_item)
                        
                        bills_created.append({
                            'bill_id': bill.id,
                            'shop_name': bill.shop_name,
                            'date': bill_date.isoformat(),
                            'item_count': len(items)
                        })
                    except Exception as e:
                        errors.append(f'Failed to create bill for {shop_name} on {date_str}: {str(e)}')
            
            else:
                # Original format: shop_name, date, total_amount, line_items
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Parse date
                        date_str = row.get('date', '')
                        try:
                            bill_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except:
                            bill_date = datetime.now().date()
                        
                        shop_name = row.get('shop_name', 'Unknown')
                        total_amount = float(row.get('total_amount', 0.0))
                        
                        # Check for duplicate bill (same shop, date, and total amount)
                        existing_bill = Bill.query.filter_by(
                            shop_name=shop_name,
                            date=bill_date,
                            total_amount=total_amount
                        ).first()
                        
                        if existing_bill:
                            # Skip this bill, it's a duplicate
                            errors.append(f'Row {row_num}: Duplicate bill skipped - {shop_name} on {bill_date.isoformat()} with total ${total_amount:.2f}')
                            continue
                        
                        # Create bill
                        bill = Bill(
                            shop_name=shop_name,
                            date=bill_date,
                            total_amount=total_amount,
                            upload_type='csv',
                            file_path=None
                        )
                        db.session.add(bill)
                        db.session.flush()
                        
                        # Parse line items (pipe-separated in CSV)
                        line_items_str = row.get('line_items', '')
                        if line_items_str:
                            items = line_items_str.split('|')
                            for item_str in items:
                                parts = item_str.split(',')
                                if len(parts) >= 3:
                                    line_item = LineItem(
                                        bill_id=bill.id,
                                        item_name=parts[0].strip(),
                                        quantity=float(parts[1].strip()) if parts[1].strip() else 1,
                                        price=float(parts[2].strip()) if parts[2].strip() else 0.0,
                                        category=parts[3].strip() if len(parts) > 3 and parts[3].strip() else 'Uncategorized'
                                    )
                                    db.session.add(line_item)
                        
                        bills_created.append({
                            'bill_id': bill.id,
                            'shop_name': bill.shop_name,
                            'date': bill_date.isoformat()
                        })
                    
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'bills_created': len(bills_created),
                'bills': bills_created,
                'errors': errors
            }), 201
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to process CSV: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/bills', methods=['GET'])
def get_bills():
    """Get all bills with optional filters"""
    month = request.args.get('month')
    year = request.args.get('year')
    
    query = Bill.query
    
    if month:
        query = query.filter(extract('month', Bill.date) == int(month))
    if year:
        query = query.filter(extract('year', Bill.date) == int(year))
    
    bills = query.order_by(Bill.date.desc()).all()
    
    result = []
    for bill in bills:
        line_items = LineItem.query.filter_by(bill_id=bill.id).all()
        result.append({
            'id': bill.id,
            'shop_name': bill.shop_name,
            'date': bill.date.isoformat(),
            'total_amount': bill.total_amount,
            'upload_type': bill.upload_type,
            'line_items': [{
                'name': item.item_name,
                'quantity': item.quantity,
                'price': item.price,
                'category': item.category
            } for item in line_items]
        })
    
    return jsonify({'bills': result}), 200

@app.route('/api/analysis/monthly', methods=['GET'])
def get_monthly_analysis():
    """Get monthly analysis breakdown"""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    if not month or not year:
        return jsonify({'error': 'Month and year are required'}), 400
    
    analysis = analysis_service.get_monthly_analysis(month, year)
    return jsonify(analysis), 200

@app.route('/api/analysis/summary', methods=['GET'])
def get_analysis_summary():
    """Get overall analysis summary"""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    summary = analysis_service.get_summary(month, year)
    return jsonify(summary), 200

@app.route('/api/bills', methods=['DELETE'])
def delete_all_bills():
    """Delete all bills from the database"""
    try:
        # Get count before deletion
        bill_count = Bill.query.count()
        line_item_count = LineItem.query.count()
        
        # Delete all bills (line items will be cascade deleted)
        Bill.query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'All bills deleted successfully',
            'bills_deleted': bill_count,
            'line_items_deleted': line_item_count
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete bills: {str(e)}'}), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(debug=debug_mode, host=host, port=port)

