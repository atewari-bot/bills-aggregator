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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bills.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'pdf', 'csv'}

# Initialize database
db.init_app(app)

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
            # Extract data using OCR
            extracted_data = ocr_service.extract_from_image(filepath)
            
            # Create bill record
            bill = Bill(
                shop_name=extracted_data.get('shop_name', 'Unknown'),
                date=extracted_data.get('date', datetime.now().date()),
                total_amount=extracted_data.get('total_amount', 0.0),
                upload_type='image',
                file_path=filepath
            )
            db.session.add(bill)
            db.session.flush()
            
            # Create line items
            line_items = []
            for item in extracted_data.get('line_items', []):
                line_item = LineItem(
                    bill_id=bill.id,
                    item_name=item.get('name', ''),
                    quantity=item.get('quantity', 1),
                    price=item.get('price', 0.0),
                    category=item.get('category', 'Uncategorized')
                )
                db.session.add(line_item)
                line_items.append({
                    'name': line_item.item_name,
                    'quantity': line_item.quantity,
                    'price': line_item.price,
                    'category': line_item.category
                })
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'bill_id': bill.id,
                'shop_name': bill.shop_name,
                'date': bill.date.isoformat(),
                'total_amount': bill.total_amount,
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
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)
            
            bills_created = []
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
                try:
                    # Parse date
                    date_str = row.get('date', '')
                    try:
                        bill_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        bill_date = datetime.now().date()
                    
                    # Create bill
                    bill = Bill(
                        shop_name=row.get('shop_name', 'Unknown'),
                        date=bill_date,
                        total_amount=float(row.get('total_amount', 0.0)),
                        upload_type='csv',
                        file_path=None
                    )
                    db.session.add(bill)
                    db.session.flush()
                    
                    # Parse line items (comma-separated in CSV)
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

