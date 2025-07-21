"""
Database Management Module - SQLite Operations with ACID Compliance

This module provides a comprehensive database abstraction layer for receipt data storage
and retrieval. Implements proper indexing, parameterized queries, and transaction management
to ensure data integrity and optimal performance.

Features:
- ACID compliant transactions
- Optimized indexing for search performance
- Parameterized queries for SQL injection prevention
- Connection pooling and resource management
- Comprehensive error handling

Author: Receipt Processing Team
Version: 1.0.0
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import threading

from .models import Receipt, CategoryEnum, CurrencyEnum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Comprehensive database manager for receipt data with ACID compliance.
    
    Provides thread-safe operations, optimized queries, and proper resource management
    for SQLite database operations. Implements the Data Access Layer (DAL) pattern
    with comprehensive CRUD operations.
    """
    
    def __init__(self, db_path: str = "receipts.db"):
        """
        Initialize database manager with connection parameters.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()  # Thread safety
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file exists and is accessible."""
        db_file = Path(self.db_path)
        if not db_file.parent.exists():
            db_file.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with proper resource cleanup.
        
        Yields:
            sqlite3.Connection: Database connection with row factory
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self):
        """
        Initialize database schema with proper indexing and constraints.
        
        Creates the receipts table with optimized indexes for search performance.
        Ensures ACID compliance and data integrity constraints.
        """
        with self.lock:
            with self.get_connection() as conn:
                # Create receipts table with comprehensive schema
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS receipts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vendor TEXT NOT NULL,
                        transaction_date DATETIME NOT NULL,
                        amount DECIMAL(10,2) NOT NULL CHECK(amount > 0),
                        category TEXT NOT NULL,
                        currency TEXT NOT NULL DEFAULT 'USD',
                        source_file TEXT NOT NULL,
                        extracted_text TEXT,
                        confidence_score REAL DEFAULT 0.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create optimized indexes for search performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_vendor ON receipts(vendor)",
                    "CREATE INDEX IF NOT EXISTS idx_date ON receipts(transaction_date)",
                    "CREATE INDEX IF NOT EXISTS idx_amount ON receipts(amount)",
                    "CREATE INDEX IF NOT EXISTS idx_category ON receipts(category)",
                    "CREATE INDEX IF NOT EXISTS idx_currency ON receipts(currency)",
                    "CREATE INDEX IF NOT EXISTS idx_confidence ON receipts(confidence_score)",
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON receipts(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_vendor_date ON receipts(vendor, transaction_date)",
                    "CREATE INDEX IF NOT EXISTS idx_category_date ON receipts(category, transaction_date)"
                ]
                
                for index_sql in indexes:
                    conn.execute(index_sql)
                
                # Create trigger for automatic updated_at timestamp
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_receipts_timestamp 
                    AFTER UPDATE ON receipts
                    BEGIN
                        UPDATE receipts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                """)
                
                conn.commit()
                logger.info("Database initialized successfully with optimized schema")
    
    def add_receipt(self, receipt: Receipt) -> int:
        """
        Add a new receipt to the database with transaction safety.
        
        Args:
            receipt: Receipt object to add
            
        Returns:
            int: ID of the newly created receipt
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO receipts (
                        vendor, transaction_date, amount, category, currency,
                        source_file, extracted_text, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    receipt.vendor,
                    receipt.transaction_date,
                    str(receipt.amount),
                    receipt.category.value,
                    receipt.currency.value,
                    receipt.source_file,
                    receipt.extracted_text,
                    receipt.confidence_score
                ))
                
                receipt_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added receipt {receipt_id} for vendor '{receipt.vendor}'")
                return receipt_id
    
    def get_receipt_by_id(self, receipt_id: int) -> Optional[Receipt]:
        """
        Retrieve a specific receipt by ID.
        
        Args:
            receipt_id: Unique identifier of the receipt
            
        Returns:
            Receipt object if found, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM receipts WHERE id = ?",
                (receipt_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_receipt(row)
            return None
    
    def get_all_receipts(self) -> List[Receipt]:
        """
        Retrieve all receipts from the database ordered by date (newest first).
        
        Returns:
            List of Receipt objects
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM receipts 
                ORDER BY transaction_date DESC, created_at DESC
            """)
            rows = cursor.fetchall()
            
            return [self._row_to_receipt(row) for row in rows]
    
    def update_receipt(self, receipt: Receipt) -> bool:
        """
        Update an existing receipt with transaction safety.
        
        Args:
            receipt: Receipt object with updated data (must have valid ID)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if not receipt.id:
            logger.error("Cannot update receipt without ID")
            return False
        
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE receipts SET
                        vendor = ?, transaction_date = ?, amount = ?, category = ?,
                        currency = ?, source_file = ?, extracted_text = ?, confidence_score = ?
                    WHERE id = ?
                """, (
                    receipt.vendor,
                    receipt.transaction_date,
                    str(receipt.amount),
                    receipt.category.value,
                    receipt.currency.value,
                    receipt.source_file,
                    receipt.extracted_text,
                    receipt.confidence_score,
                    receipt.id
                ))
                
                success = cursor.rowcount > 0
                if success:
                    conn.commit()
                    logger.info(f"Updated receipt {receipt.id}")
                else:
                    logger.warning(f"No receipt found with ID {receipt.id}")
                
                return success
    
    def delete_receipt(self, receipt_id: int) -> bool:
        """
        Delete a receipt by ID with transaction safety.
        
        Args:
            receipt_id: Unique identifier of the receipt to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM receipts WHERE id = ?",
                    (receipt_id,)
                )
                
                success = cursor.rowcount > 0
                if success:
                    conn.commit()
                    logger.info(f"Deleted receipt {receipt_id}")
                else:
                    logger.warning(f"No receipt found with ID {receipt_id}")
                
                return success
    
    def search_receipts(
        self,
        vendor: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        amount_min: Optional[Decimal] = None,
        amount_max: Optional[Decimal] = None,
        category: Optional[CategoryEnum] = None,
        currency: Optional[CurrencyEnum] = None
    ) -> List[Receipt]:
        """
        Search receipts with multiple criteria using optimized database queries.
        
        Args:
            vendor: Vendor name (partial match supported)
            date_from: Start date for date range
            date_to: End date for date range
            amount_min: Minimum amount
            amount_max: Maximum amount
            category: Receipt category
            currency: Currency type
            
        Returns:
            List of matching Receipt objects
        """
        conditions = []
        params = []
        
        # Build dynamic WHERE clause
        if vendor:
            conditions.append("vendor LIKE ?")
            params.append(f"%{vendor}%")
        
        if date_from:
            conditions.append("transaction_date >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("transaction_date <= ?")
            params.append(date_to)
        
        if amount_min is not None:
            conditions.append("amount >= ?")
            params.append(str(amount_min))
        
        if amount_max is not None:
            conditions.append("amount <= ?")
            params.append(str(amount_max))
        
        if category:
            conditions.append("category = ?")
            params.append(category.value)
        
        if currency:
            conditions.append("currency = ?")
            params.append(currency.value)
        
        # Construct query
        base_query = "SELECT * FROM receipts"
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            query = base_query + where_clause + " ORDER BY transaction_date DESC"
        else:
            query = base_query + " ORDER BY transaction_date DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_receipt(row) for row in rows]
    
    def get_vendor_statistics(self) -> List[Tuple[str, int, Decimal]]:
        """
        Get vendor statistics (name, count, total amount) ordered by total spending.
        
        Returns:
            List of tuples (vendor_name, transaction_count, total_amount)
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT vendor, COUNT(*) as count, SUM(amount) as total
                FROM receipts
                GROUP BY vendor
                ORDER BY total DESC
            """)
            rows = cursor.fetchall()
            
            return [(row['vendor'], row['count'], Decimal(str(row['total']))) for row in rows]
    
    def get_monthly_statistics(self) -> List[Tuple[str, int, Decimal]]:
        """
        Get monthly spending statistics ordered by month.
        
        Returns:
            List of tuples (month_year, transaction_count, total_amount)
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT strftime('%Y-%m', transaction_date) as month,
                       COUNT(*) as count,
                       SUM(amount) as total
                FROM receipts
                GROUP BY strftime('%Y-%m', transaction_date)
                ORDER BY month DESC
            """)
            rows = cursor.fetchall()
            
            return [(row['month'], row['count'], Decimal(str(row['total']))) for row in rows]
    
    def get_category_statistics(self) -> List[Tuple[str, int, Decimal]]:
        """
        Get category statistics ordered by total spending.
        
        Returns:
            List of tuples (category, transaction_count, total_amount)
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count, SUM(amount) as total
                FROM receipts
                GROUP BY category
                ORDER BY total DESC
            """)
            rows = cursor.fetchall()
            
            return [(row['category'], row['count'], Decimal(str(row['total']))) for row in rows]
    
    def bulk_delete_receipts(self, receipt_ids: List[int]) -> int:
        """
        Delete multiple receipts in a single transaction.
        
        Args:
            receipt_ids: List of receipt IDs to delete
            
        Returns:
            int: Number of receipts actually deleted
        """
        if not receipt_ids:
            return 0
        
        with self.lock:
            with self.get_connection() as conn:
                placeholders = ','.join('?' * len(receipt_ids))
                cursor = conn.execute(
                    f"DELETE FROM receipts WHERE id IN ({placeholders})",
                    receipt_ids
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Bulk deleted {deleted_count} receipts")
                return deleted_count
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics for monitoring and analytics.
        
        Returns:
            Dictionary with database statistics
        """
        with self.get_connection() as conn:
            stats = {}
            
            # Basic counts
            cursor = conn.execute("SELECT COUNT(*) as total FROM receipts")
            stats['total_receipts'] = cursor.fetchone()['total']
            
            cursor = conn.execute("SELECT SUM(amount) as total FROM receipts")
            total_amount = cursor.fetchone()['total']
            stats['total_amount'] = Decimal(str(total_amount)) if total_amount else Decimal('0.00')
            
            cursor = conn.execute("SELECT AVG(amount) as avg FROM receipts")
            avg_amount = cursor.fetchone()['avg']
            stats['average_amount'] = Decimal(str(avg_amount)) if avg_amount else Decimal('0.00')
            
            # Date range
            cursor = conn.execute("""
                SELECT MIN(transaction_date) as earliest, MAX(transaction_date) as latest
                FROM receipts
            """)
            date_range = cursor.fetchone()
            stats['date_range'] = {
                'earliest': date_range['earliest'],
                'latest': date_range['latest']
            }
            
            # Unique counts
            cursor = conn.execute("SELECT COUNT(DISTINCT vendor) as count FROM receipts")
            stats['unique_vendors'] = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(DISTINCT category) as count FROM receipts")
            stats['unique_categories'] = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(DISTINCT currency) as count FROM receipts")
            stats['unique_currencies'] = cursor.fetchone()['count']
            
            return stats
    
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
            transaction_date=datetime.fromisoformat(row['transaction_date']),
            amount=Decimal(str(row['amount'])),
            category=CategoryEnum(row['category']),
            currency=CurrencyEnum(row['currency']),
            source_file=row['source_file'],
            extracted_text=row['extracted_text'],
            confidence_score=row['confidence_score']
        )
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for the backup file
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            with self.get_connection() as source:
                backup_conn = sqlite3.connect(backup_path)
                source.backup(backup_conn)
                backup_conn.close()
                
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def optimize_database(self):
        """
        Optimize database performance by running VACUUM and ANALYZE.
        """
        with self.lock:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                conn.commit()
                
            logger.info("Database optimization completed")
