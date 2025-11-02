from flask_sqlalchemy import SQLAlchemy
from datetime import date
from decimal import Decimal

db = SQLAlchemy()

class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    upload_type = db.Column(db.String(20), nullable=False)  # 'image' or 'csv'
    file_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    line_items = db.relationship('LineItem', backref='bill', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'shop_name': self.shop_name,
            'date': self.date.isoformat(),
            'total_amount': float(self.total_amount),
            'upload_type': self.upload_type,
            'line_items': [item.to_dict() for item in self.line_items]
        }

class LineItem(db.Model):
    __tablename__ = 'line_items'
    
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100), nullable=False, default='Uncategorized')
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'quantity': float(self.quantity),
            'price': float(self.price),
            'category': self.category
        }

