"""
Database layer for receipt processing application.
Implements SQLite database with proper indexing and ACID compliance.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from .models import Receipt, SearchFilters, AnalyticsData


class DatabaseError(Exception):
    """Custom database exception."""
    pass


class ReceiptDatabase:
    """
    Data Access Layer for receipt management.
    
    Provides CRUD operations, search functionality, and analytics queries
    with proper error handling and connection management.
    """
    
    def __init__(self, db_path: str = "receipts.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database schema and indexes."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create receipts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS receipts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vendor TEXT NOT NULL,
                        transaction_date DATE NOT NULL,
                        amount DECIMAL(10,2) NOT NULL CHECK(amount > 0),
                        category TEXT NOT NULL DEFAULT 'Other',
                        currency TEXT NOT NULL DEFAULT 'USD',
                        source_file TEXT NOT NULL,
                        extracted_text TEXT,
                        confidence_score REAL DEFAULT 0.0 CHECK(confidence_score >= 0 AND confidence_score <= 100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_vendor ON receipts(vendor)",
                    "CREATE INDEX IF NOT EXISTS idx_date ON receipts(transaction_date)",
                    "CREATE INDEX IF NOT EXISTS idx_amount ON receipts(amount)",
                    "CREATE INDEX IF NOT EXISTS idx_category ON receipts(category)",
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON receipts(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_vendor_date ON receipts(vendor, transaction_date)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        Ensures proper connection handling and cleanup.
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def add_receipt(self, receipt: Receipt) -> int:
        """
        Add a new receipt to the database.
        
        Args:
            receipt: Receipt object to add
            
        Returns:
            int: ID of the inserted receipt
            
        Raises:
            DatabaseError: If insertion fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO receipts (
                        vendor, transaction_date, amount, category, currency,
                        source_file, extracted_text, confidence_score, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    receipt.vendor,
                    receipt.transaction_date,
                    float(receipt.amount),
                    receipt.category,
                    receipt.currency,
                    receipt.source_file,
                    receipt.extracted_text,
                    receipt.confidence_score,
                    receipt.created_at or datetime.now(),
                    receipt.updated_at or datetime.now()
                ))
                
                receipt_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Receipt added successfully with ID: {receipt_id}")
                return receipt_id
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to add receipt: {e}")
            raise DatabaseError(f"Failed to add receipt: {e}")
    
    def get_receipt(self, receipt_id: int) -> Optional[Receipt]:
        """
        Retrieve a receipt by ID.
        
        Args:
            receipt_id: Receipt ID to retrieve
            
        Returns:
            Receipt object or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_receipt(row)
                return None
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get receipt {receipt_id}: {e}")
            raise DatabaseError(f"Failed to retrieve receipt: {e}")
    
    def get_all_receipts(self, limit: Optional[int] = None, offset: int = 0) -> List[Receipt]:
        """
        Retrieve all receipts with optional pagination.
        
        Args:
            limit: Maximum number of receipts to return
            offset: Number of receipts to skip
            
        Returns:
            List of Receipt objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM receipts ORDER BY transaction_date DESC, created_at DESC"
                params = []
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_receipt(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get receipts: {e}")
            raise DatabaseError(f"Failed to retrieve receipts: {e}")
    
    def search_receipts(self, filters: SearchFilters) -> List[Receipt]:
        """
        Search receipts based on filters.
        
        Args:
            filters: SearchFilters object with search criteria
            
        Returns:
            List of matching Receipt objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM receipts WHERE 1=1"
                params = []
                
                # Build dynamic query based on filters
                if filters.vendor_query:
                    query += " AND vendor LIKE ?"
                    params.append(f"%{filters.vendor_query}%")
                
                if filters.date_from:
                    query += " AND transaction_date >= ?"
                    params.append(filters.date_from)
                
                if filters.date_to:
                    query += " AND transaction_date <= ?"
                    params.append(filters.date_to)
                
                if filters.amount_min:
                    query += " AND amount >= ?"
                    params.append(float(filters.amount_min))
                
                if filters.amount_max:
                    query += " AND amount <= ?"
                    params.append(float(filters.amount_max))
                
                if filters.category:
                    query += " AND category = ?"
                    params.append(filters.category)
                
                if filters.currency:
                    query += " AND currency = ?"
                    params.append(filters.currency)
                
                query += " ORDER BY transaction_date DESC, created_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_receipt(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to search receipts: {e}")
            raise DatabaseError(f"Failed to search receipts: {e}")
    
    def update_receipt(self, receipt: Receipt) -> bool:
        """
        Update an existing receipt.
        
        Args:
            receipt: Receipt object with updated data
            
        Returns:
            bool: True if update successful, False if receipt not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE receipts SET
                        vendor = ?, transaction_date = ?, amount = ?, category = ?,
                        currency = ?, source_file = ?, extracted_text = ?,
                        confidence_score = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    receipt.vendor,
                    receipt.transaction_date,
                    float(receipt.amount),
                    receipt.category,
                    receipt.currency,
                    receipt.source_file,
                    receipt.extracted_text,
                    receipt.confidence_score,
                    datetime.now(),
                    receipt.id
                ))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    self.logger.info(f"Receipt {receipt.id} updated successfully")
                else:
                    self.logger.warning(f"Receipt {receipt.id} not found for update")
                
                return success
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update receipt {receipt.id}: {e}")
            raise DatabaseError(f"Failed to update receipt: {e}")
    
    def delete_receipt(self, receipt_id: int) -> bool:
        """
        Delete a receipt by ID.
        
        Args:
            receipt_id: ID of receipt to delete
            
        Returns:
            bool: True if deletion successful, False if receipt not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    self.logger.info(f"Receipt {receipt_id} deleted successfully")
                else:
                    self.logger.warning(f"Receipt {receipt_id} not found for deletion")
                
                return success
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete receipt {receipt_id}: {e}")
            raise DatabaseError(f"Failed to delete receipt: {e}")
    
    def get_analytics(self) -> AnalyticsData:
        """
        Generate analytics data from receipts.
        
        Returns:
            AnalyticsData object with statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Basic statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_receipts,
                        COALESCE(SUM(amount), 0) as total_amount,
                        COALESCE(AVG(amount), 0) as average_amount,
                        MIN(transaction_date) as earliest_date,
                        MAX(transaction_date) as latest_date
                    FROM receipts
                """)
                stats = cursor.fetchone()
                
                # Top vendors
                cursor.execute("""
                    SELECT vendor, COUNT(*) as count, SUM(amount) as total_amount
                    FROM receipts
                    GROUP BY vendor
                    ORDER BY total_amount DESC
                    LIMIT 10
                """)
                top_vendors = [
                    {"vendor": row[0], "count": row[1], "total_amount": float(row[2])}
                    for row in cursor.fetchall()
                ]
                
                # Category breakdown
                cursor.execute("""
                    SELECT category, COUNT(*) as count, SUM(amount) as total_amount
                    FROM receipts
                    GROUP BY category
                    ORDER BY total_amount DESC
                """)
                category_breakdown = [
                    {"category": row[0], "count": row[1], "total_amount": float(row[2])}
                    for row in cursor.fetchall()
                ]
                
                # Monthly trends
                cursor.execute("""
                    SELECT 
                        strftime('%Y-%m', transaction_date) as month,
                        COUNT(*) as count,
                        SUM(amount) as total_amount
                    FROM receipts
                    GROUP BY strftime('%Y-%m', transaction_date)
                    ORDER BY month DESC
                    LIMIT 12
                """)
                monthly_trends = [
                    {"month": row[0], "count": row[1], "total_amount": float(row[2])}
                    for row in cursor.fetchall()
                ]
                
                return AnalyticsData(
                    total_receipts=stats[0],
                    total_amount=Decimal(str(stats[1])),
                    average_amount=Decimal(str(stats[2])),
                    date_range=(stats[3], stats[4]) if stats[3] and stats[4] else None,
                    top_vendors=top_vendors,
                    category_breakdown=category_breakdown,
                    monthly_trends=monthly_trends
                )
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to generate analytics: {e}")
            raise DatabaseError(f"Failed to generate analytics: {e}")
    
    def _row_to_receipt(self, row: sqlite3.Row) -> Receipt:
        """
        Convert database row to Receipt object.
        
        Args:
            row: SQLite row object
            
        Returns:
            Receipt object
        """
        return Receipt(
            id=row['id'],
            vendor=row['vendor'],
            transaction_date=row['transaction_date'],
            amount=Decimal(str(row['amount'])),
            category=row['category'],
            currency=row['currency'],
            source_file=row['source_file'],
            extracted_text=row['extracted_text'],
            confidence_score=row['confidence_score'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def get_receipt_count(self) -> int:
        """Get total number of receipts."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM receipts")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get receipt count: {e}")
            return 0
