import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .models import Receipt, ReceiptItem, ReceiptStatistics

class ReceiptDatabase:
    """Database manager for receipts"""
    
    def __init__(self, db_path: str = "data/receipts.db"):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create receipts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    total REAL NOT NULL,
                    items TEXT,
                    category TEXT DEFAULT 'Other',
                    tax REAL DEFAULT 0.0,
                    tip REAL DEFAULT 0.0,
                    payment_method TEXT DEFAULT 'Unknown',
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_receipts_store ON receipts(store_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_receipts_category ON receipts(category)')
            
            conn.commit()
    
    def add_receipt(self, receipt: Receipt) -> int:
        """Add a new receipt to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Serialize items to JSON
            items_json = json.dumps([item.to_dict() for item in receipt.items])
            
            cursor.execute('''
                INSERT INTO receipts (
                    store_name, date, total, items, category, tax, tip, 
                    payment_method, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                receipt.store_name,
                receipt.date.isoformat(),
                receipt.total,
                items_json,
                receipt.category,
                receipt.tax,
                receipt.tip,
                receipt.payment_method,
                receipt.created_at.isoformat() if receipt.created_at else datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            receipt_id = cursor.lastrowid
            conn.commit()
            
            return receipt_id
    
    def get_receipt(self, receipt_id: int) -> Optional[Receipt]:
        """Get a receipt by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM receipts WHERE id = ?', (receipt_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_receipt(row)
            return None
    
    def get_all_receipts(self) -> List[Receipt]:
        """Get all receipts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM receipts ORDER BY date DESC')
            rows = cursor.fetchall()
            
            return [self._row_to_receipt(row) for row in rows]
    
    def get_recent_receipts(self, limit: int = 10) -> List[Receipt]:
        """Get recent receipts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM receipts ORDER BY created_at DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            
            return [self._row_to_receipt(row) for row in rows]
    
    def get_receipts_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Receipt]:
        """Get receipts within a date range"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM receipts 
                WHERE date BETWEEN ? AND ? 
                ORDER BY date DESC
            ''', (start_date.isoformat(), end_date.isoformat()))
            
            rows = cursor.fetchall()
            return [self._row_to_receipt(row) for row in rows]
    
    def get_receipts_by_store(self, store_name: str) -> List[Receipt]:
        """Get receipts from a specific store"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM receipts 
                WHERE store_name LIKE ? 
                ORDER BY date DESC
            ''', (f'%{store_name}%',))
            
            rows = cursor.fetchall()
            return [self._row_to_receipt(row) for row in rows]
    
    def get_receipts_by_category(self, category: str) -> List[Receipt]:
        """Get receipts by category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM receipts 
                WHERE category = ? 
                ORDER BY date DESC
            ''', (category,))
            
            rows = cursor.fetchall()
            return [self._row_to_receipt(row) for row in rows]
    
    def update_receipt(self, receipt: Receipt) -> bool:
        """Update an existing receipt"""
        if not receipt.receipt_id:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            items_json = json.dumps([item.to_dict() for item in receipt.items])
            
            cursor.execute('''
                UPDATE receipts SET
                    store_name = ?, date = ?, total = ?, items = ?, 
                    category = ?, tax = ?, tip = ?, payment_method = ?, 
                    updated_at = ?
                WHERE id = ?
            ''', (
                receipt.store_name,
                receipt.date.isoformat(),
                receipt.total,
                items_json,
                receipt.category,
                receipt.tax,
                receipt.tip,
                receipt.payment_method,
                datetime.now().isoformat(),
                receipt.receipt_id
            ))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_receipt(self, receipt_id: int) -> bool:
        """Delete a receipt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM receipts WHERE id = ?', (receipt_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_statistics(self) -> ReceiptStatistics:
        """Get receipt statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = ReceiptStatistics()
            
            # Total receipts and spending
            cursor.execute('SELECT COUNT(*), SUM(total), AVG(total), MAX(total) FROM receipts')
            row = cursor.fetchone()
            if row and row[0]:
                stats.total_receipts = row[0]
                stats.total_spent = row[1] or 0.0
                stats.average_receipt = row[2] or 0.0
                stats.most_expensive_receipt = row[3] or 0.0
            
            # Most frequent store
            cursor.execute('''
                SELECT store_name, COUNT(*) as count 
                FROM receipts 
                GROUP BY store_name 
                ORDER BY count DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                stats.most_frequent_store = row[0]
            
            # This month's statistics
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            cursor.execute('''
                SELECT COUNT(*), SUM(total) 
                FROM receipts 
                WHERE date >= ?
            ''', (current_month.isoformat(),))
            row = cursor.fetchone()
            if row:
                stats.receipts_this_month = row[0] or 0
                stats.spending_this_month = row[1] or 0.0
            
            return stats
    
    def get_spending_by_category(self) -> List[Dict[str, Any]]:
        """Get spending breakdown by category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category, COUNT(*) as count, SUM(total) as total
                FROM receipts 
                GROUP BY category 
                ORDER BY total DESC
            ''')
            
            rows = cursor.fetchall()
            return [
                {
                    'category': row[0],
                    'count': row[1],
                    'total': row[2]
                }
                for row in rows
            ]
    
    def get_spending_by_month(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get spending by month"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m', date) as month,
                    COUNT(*) as count,
                    SUM(total) as total
                FROM receipts 
                WHERE date >= date('now', '-{} months')
                GROUP BY strftime('%Y-%m', date)
                ORDER BY month DESC
            '''.format(months))
            
            rows = cursor.fetchall()
            return [
                {
                    'month': row[0],
                    'count': row[1],
                    'total': row[2]
                }
                for row in rows
            ]
    
    def search_receipts(self, query: str) -> List[Receipt]:
        """Search receipts by store name or items"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM receipts 
                WHERE store_name LIKE ? OR items LIKE ?
                ORDER BY date DESC
            ''', (f'%{query}%', f'%{query}%'))
            
            rows = cursor.fetchall()
            return [self._row_to_receipt(row) for row in rows]
    
    def _row_to_receipt(self, row) -> Receipt:
        """Convert database row to Receipt object"""
        # Parse items from JSON
        items = []
        if row[4]:  # items column
            try:
                items_data = json.loads(row[4])
                items = [ReceiptItem.from_dict(item) for item in items_data]
            except (json.JSONDecodeError, TypeError):
                items = []
        
        # Parse date
        try:
            date = datetime.fromisoformat(row[2])
        except ValueError:
            date = datetime.now()
        
        # Parse created_at
        try:
            created_at = datetime.fromisoformat(row[9]) if row[9] else datetime.now()
        except ValueError:
            created_at = datetime.now()
        
        return Receipt(
            receipt_id=row[0],
            store_name=row[1],
            date=date,
            total=row[3],
            items=items,
            category=row[5] or 'Other',
            tax=row[6] or 0.0,
            tip=row[7] or 0.0,
            payment_method=row[8] or 'Unknown',
            created_at=created_at
        )
    
    def close(self):
        """Close database connection (if needed)"""
        pass  # Using context managers, so no explicit close needed
