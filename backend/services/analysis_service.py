from sqlalchemy import func, extract
from datetime import datetime
from models import db, Bill, LineItem

class AnalysisService:
    """Service for analyzing bills and generating reports"""
    
    def get_monthly_analysis(self, month, year):
        """Get detailed monthly analysis"""
        # Get all bills for the month
        bills = Bill.query.filter(
            extract('month', Bill.date) == month,
            extract('year', Bill.date) == year
        ).all()
        
        # Analysis by shop
        shop_stats = db.session.query(
            Bill.shop_name,
            func.count(Bill.id).label('bill_count'),
            func.sum(Bill.total_amount).label('total_spent')
        ).filter(
            extract('month', Bill.date) == month,
            extract('year', Bill.date) == year
        ).group_by(Bill.shop_name).all()
        
        shops = [{
            'shop_name': stat.shop_name,
            'bill_count': stat.bill_count,
            'total_spent': float(stat.total_spent) if stat.total_spent else 0.0
        } for stat in shop_stats]
        
        # Analysis by item category
        category_stats = db.session.query(
            LineItem.category,
            func.count(LineItem.id).label('item_count'),
            func.sum(LineItem.price * LineItem.quantity).label('total_spent')
        ).join(Bill).filter(
            extract('month', Bill.date) == month,
            extract('year', Bill.date) == year
        ).group_by(LineItem.category).all()
        
        categories = [{
            'category': stat.category,
            'item_count': stat.item_count,
            'total_spent': float(stat.total_spent) if stat.total_spent else 0.0
        } for stat in category_stats]
        
        # Top items
        item_stats = db.session.query(
            LineItem.item_name,
            func.sum(LineItem.quantity).label('total_quantity'),
            func.sum(LineItem.price * LineItem.quantity).label('total_spent'),
            func.count(LineItem.id).label('purchase_count')
        ).join(Bill).filter(
            extract('month', Bill.date) == month,
            extract('year', Bill.date) == year
        ).group_by(LineItem.item_name).order_by(
            func.sum(LineItem.price * LineItem.quantity).desc()
        ).limit(20).all()
        
        top_items = [{
            'item_name': stat.item_name,
            'total_quantity': float(stat.total_quantity) if stat.total_quantity else 0.0,
            'total_spent': float(stat.total_spent) if stat.total_spent else 0.0,
            'purchase_count': stat.purchase_count
        } for stat in item_stats]
        
        # Calculate totals
        total_bills = len(bills)
        total_spent = sum(float(bill.total_amount) for bill in bills)
        
        return {
            'month': month,
            'year': year,
            'total_bills': total_bills,
            'total_spent': total_spent,
            'shops': shops,
            'categories': categories,
            'top_items': top_items
        }
    
    def get_summary(self, month=None, year=None):
        """Get overall summary with optional month/year filter"""
        query = Bill.query
        
        if month:
            query = query.filter(extract('month', Bill.date) == month)
        if year:
            query = query.filter(extract('year', Bill.date) == year)
        
        bills = query.all()
        
        total_bills = len(bills)
        total_spent = sum(float(bill.total_amount) for bill in bills) if bills else 0.0
        
        # Get unique shops
        unique_shops = db.session.query(func.distinct(Bill.shop_name)).count()
        
        # Get total items
        line_item_query = LineItem.query.join(Bill)
        if month:
            line_item_query = line_item_query.filter(extract('month', Bill.date) == month)
        if year:
            line_item_query = line_item_query.filter(extract('year', Bill.date) == year)
        
        total_items = line_item_query.count()
        
        # Average bill amount
        avg_bill_amount = total_spent / total_bills if total_bills > 0 else 0.0
        
        return {
            'total_bills': total_bills,
            'total_spent': total_spent,
            'unique_shops': unique_shops,
            'total_items': total_items,
            'avg_bill_amount': avg_bill_amount,
            'filter': {
                'month': month,
                'year': year
            }
        }

