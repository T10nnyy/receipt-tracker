"""
Database Module Tests - Comprehensive Test Suite

This module contains comprehensive unit tests for the database operations
including CRUD operations, search functionality, and data integrity validation.

Author: Receipt Processing Team
Version: 1.0.0
"""

import unittest
import tempfile
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Import modules to test
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.database import DatabaseManager
from core.models import Receipt, CategoryEnum, CurrencyEnum

class TestDatabaseManager(unittest.TestCase):
    """Test suite for DatabaseManager class."""
    
    def setUp(self):
        """Set up test database for each test."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database manager with temp database
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.db_manager.initialize_database()
        
        # Create sample receipt for testing
        self.sample_receipt = Receipt(
            vendor="Test Vendor",
            transaction_date=datetime(2024, 1, 15, 10, 30),
            amount=Decimal("25.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="test_receipt.pdf",
            extracted_text="Test receipt text content",
            confidence_score=0.95
        )
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary database file
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization and schema creation."""
        # Database should be initialized without errors
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Test that we can connect to the database
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='receipts'")
            table_exists = cursor.fetchone() is not None
            self.assertTrue(table_exists)
    
    def test_add_receipt(self):
        """Test adding a new receipt to the database."""
        # Add receipt
        receipt_id = self.db_manager.add_receipt(self.sample_receipt)
        
        # Verify receipt was added
        self.assertIsInstance(receipt_id, int)
        self.assertGreater(receipt_id, 0)
        
        # Verify receipt can be retrieved
        retrieved_receipt = self.db_manager.get_receipt_by_id(receipt_id)
        self.assertIsNotNone(retrieved_receipt)
        self.assertEqual(retrieved_receipt.vendor, self.sample_receipt.vendor)
        self.assertEqual(retrieved_receipt.amount, self.sample_receipt.amount)
    
    def test_get_receipt_by_id(self):
        """Test retrieving a receipt by ID."""
        # Add receipt first
        receipt_id = self.db_manager.add_receipt(self.sample_receipt)
        
        # Retrieve receipt
        retrieved_receipt = self.db_manager.get_receipt_by_id(receipt_id)
        
        # Verify receipt data
        self.assertIsNotNone(retrieved_receipt)
        self.assertEqual(retrieved_receipt.id, receipt_id)
        self.assertEqual(retrieved_receipt.vendor, "Test Vendor")
        self.assertEqual(retrieved_receipt.amount, Decimal("25.99"))
        self.assertEqual(retrieved_receipt.category, CategoryEnum.GROCERIES)
        self.assertEqual(retrieved_receipt.currency, CurrencyEnum.USD)
        self.assertEqual(retrieved_receipt.confidence_score, 0.95)
    
    def test_get_nonexistent_receipt(self):
        """Test retrieving a non-existent receipt."""
        # Try to get receipt with non-existent ID
        retrieved_receipt = self.db_manager.get_receipt_by_id(99999)
        
        # Should return None
        self.assertIsNone(retrieved_receipt)
    
    def test_get_all_receipts(self):
        """Test retrieving all receipts."""
        # Initially should be empty
        receipts = self.db_manager.get_all_receipts()
        self.assertEqual(len(receipts), 0)
        
        # Add multiple receipts
        receipt1 = self.sample_receipt
        receipt2 = Receipt(
            vendor="Another Vendor",
            transaction_date=datetime(2024, 1, 20, 14, 15),
            amount=Decimal("15.50"),
            category=CategoryEnum.RESTAURANTS,
            currency=CurrencyEnum.USD,
            source_file="test_receipt2.jpg",
            extracted_text="Another test receipt",
            confidence_score=0.88
        )
        
        self.db_manager.add_receipt(receipt1)
        self.db_manager.add_receipt(receipt2)
        
        # Retrieve all receipts
        all_receipts = self.db_manager.get_all_receipts()
        
        # Verify count and order (should be newest first)
        self.assertEqual(len(all_receipts), 2)
        self.assertEqual(all_receipts[0].vendor, "Another Vendor")  # Newer date
        self.assertEqual(all_receipts[1].vendor, "Test Vendor")     # Older date
    
    def test_update_receipt(self):
        """Test updating an existing receipt."""
        # Add receipt first
        receipt_id = self.db_manager.add_receipt(self.sample_receipt)
        
        # Retrieve and modify receipt
        receipt = self.db_manager.get_receipt_by_id(receipt_id)
        receipt.vendor = "Updated Vendor"
        receipt.amount = Decimal("30.00")
        receipt.category = CategoryEnum.SHOPPING
        
        # Update receipt
        success = self.db_manager.update_receipt(receipt)
        self.assertTrue(success)
        
        # Verify update
        updated_receipt = self.db_manager.get_receipt_by_id(receipt_id)
        self.assertEqual(updated_receipt.vendor, "Updated Vendor")
        self.assertEqual(updated_receipt.amount, Decimal("30.00"))
        self.assertEqual(updated_receipt.category, CategoryEnum.SHOPPING)
    
    def test_update_nonexistent_receipt(self):
        """Test updating a non-existent receipt."""
        # Create receipt with non-existent ID
        fake_receipt = self.sample_receipt
        fake_receipt.id = 99999
        
        # Try to update
        success = self.db_manager.update_receipt(fake_receipt)
        self.assertFalse(success)
    
    def test_delete_receipt(self):
        """Test deleting a receipt."""
        # Add receipt first
        receipt_id = self.db_manager.add_receipt(self.sample_receipt)
        
        # Verify receipt exists
        self.assertIsNotNone(self.db_manager.get_receipt_by_id(receipt_id))
        
        # Delete receipt
        success = self.db_manager.delete_receipt(receipt_id)
        self.assertTrue(success)
        
        # Verify receipt is gone
        self.assertIsNone(self.db_manager.get_receipt_by_id(receipt_id))
    
    def test_delete_nonexistent_receipt(self):
        """Test deleting a non-existent receipt."""
        # Try to delete non-existent receipt
        success = self.db_manager.delete_receipt(99999)
        self.assertFalse(success)
    
    def test_search_receipts_by_vendor(self):
        """Test searching receipts by vendor name."""
        # Add multiple receipts
        receipt1 = Receipt(
            vendor="Walmart",
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal("25.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="walmart.pdf",
            extracted_text="Walmart receipt",
            confidence_score=0.95
        )
        
        receipt2 = Receipt(
            vendor="Target",
            transaction_date=datetime(2024, 1, 16),
            amount=Decimal("35.50"),
            category=CategoryEnum.SHOPPING,
            currency=CurrencyEnum.USD,
            source_file="target.pdf",
            extracted_text="Target receipt",
            confidence_score=0.90
        )
        
        self.db_manager.add_receipt(receipt1)
        self.db_manager.add_receipt(receipt2)
        
        # Search for Walmart receipts
        walmart_receipts = self.db_manager.search_receipts(vendor="Walmart")
        self.assertEqual(len(walmart_receipts), 1)
        self.assertEqual(walmart_receipts[0].vendor, "Walmart")
        
        # Search with partial match
        partial_receipts = self.db_manager.search_receipts(vendor="Wal")
        self.assertEqual(len(partial_receipts), 1)
        self.assertEqual(partial_receipts[0].vendor, "Walmart")
    
    def test_search_receipts_by_date_range(self):
        """Test searching receipts by date range."""
        # Add receipts with different dates
        receipt1 = Receipt(
            vendor="Store A",
            transaction_date=datetime(2024, 1, 10),
            amount=Decimal("20.00"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="store_a.pdf",
            extracted_text="Store A receipt",
            confidence_score=0.95
        )
        
        receipt2 = Receipt(
            vendor="Store B",
            transaction_date=datetime(2024, 1, 20),
            amount=Decimal("30.00"),
            category=CategoryEnum.SHOPPING,
            currency=CurrencyEnum.USD,
            source_file="store_b.pdf",
            extracted_text="Store B receipt",
            confidence_score=0.90
        )
        
        receipt3 = Receipt(
            vendor="Store C",
            transaction_date=datetime(2024, 1, 30),
            amount=Decimal("40.00"),
            category=CategoryEnum.RESTAURANTS,
            currency=CurrencyEnum.USD,
            source_file="store_c.pdf",
            extracted_text="Store C receipt",
            confidence_score=0.85
        )
        
        self.db_manager.add_receipt(receipt1)
        self.db_manager.add_receipt(receipt2)
        self.db_manager.add_receipt(receipt3)
        
        # Search for receipts in middle of January
        mid_january_receipts = self.db_manager.search_receipts(
            date_from=datetime(2024, 1, 15),
            date_to=datetime(2024, 1, 25)
        )
        
        self.assertEqual(len(mid_january_receipts), 1)
        self.assertEqual(mid_january_receipts[0].vendor, "Store B")
    
    def test_search_receipts_by_amount_range(self):
        """Test searching receipts by amount range."""
        # Add receipts with different amounts
        receipt1 = Receipt(
            vendor="Cheap Store",
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal("5.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="cheap.pdf",
            extracted_text="Cheap receipt",
            confidence_score=0.95
        )
        
        receipt2 = Receipt(
            vendor="Mid Store",
            transaction_date=datetime(2024, 1, 16),
            amount=Decimal("25.50"),
            category=CategoryEnum.SHOPPING,
            currency=CurrencyEnum.USD,
            source_file="mid.pdf",
            extracted_text="Mid receipt",
            confidence_score=0.90
        )
        
        receipt3 = Receipt(
            vendor="Expensive Store",
            transaction_date=datetime(2024, 1, 17),
            amount=Decimal("99.99"),
            category=CategoryEnum.ELECTRONICS,
            currency=CurrencyEnum.USD,
            source_file="expensive.pdf",
            extracted_text="Expensive receipt",
            confidence_score=0.85
        )
        
        self.db_manager.add_receipt(receipt1)
        self.db_manager.add_receipt(receipt2)
        self.db_manager.add_receipt(receipt3)
        
        # Search for mid-range receipts
        mid_range_receipts = self.db_manager.search_receipts(
            amount_min=Decimal("10.00"),
            amount_max=Decimal("50.00")
        )
        
        self.assertEqual(len(mid_range_receipts), 1)
        self.assertEqual(mid_range_receipts[0].vendor, "Mid Store")
    
    def test_search_receipts_by_category(self):
        """Test searching receipts by category."""
        # Add receipts with different categories
        receipt1 = Receipt(
            vendor="Grocery Store",
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal("25.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="grocery.pdf",
            extracted_text="Grocery receipt",
            confidence_score=0.95
        )
        
        receipt2 = Receipt(
            vendor="Restaurant",
            transaction_date=datetime(2024, 1, 16),
            amount=Decimal("35.50"),
            category=CategoryEnum.RESTAURANTS,
            currency=CurrencyEnum.USD,
            source_file="restaurant.pdf",
            extracted_text="Restaurant receipt",
            confidence_score=0.90
        )
        
        self.db_manager.add_receipt(receipt1)
        self.db_manager.add_receipt(receipt2)
        
        # Search for grocery receipts
        grocery_receipts = self.db_manager.search_receipts(category=CategoryEnum.GROCERIES)
        self.assertEqual(len(grocery_receipts), 1)
        self.assertEqual(grocery_receipts[0].category, CategoryEnum.GROCERIES)
    
    def test_bulk_delete_receipts(self):
        """Test bulk deletion of receipts."""
        # Add multiple receipts
        receipt_ids = []
        for i in range(5):
            receipt = Receipt(
                vendor=f"Store {i}",
                transaction_date=datetime(2024, 1, 15 + i),
                amount=Decimal(f"{10 + i}.99"),
                category=CategoryEnum.GROCERIES,
                currency=CurrencyEnum.USD,
                source_file=f"store_{i}.pdf",
                extracted_text=f"Store {i} receipt",
                confidence_score=0.90
            )
            receipt_id = self.db_manager.add_receipt(receipt)
            receipt_ids.append(receipt_id)
        
        # Verify all receipts exist
        self.assertEqual(len(self.db_manager.get_all_receipts()), 5)
        
        # Delete first 3 receipts
        deleted_count = self.db_manager.bulk_delete_receipts(receipt_ids[:3])
        self.assertEqual(deleted_count, 3)
        
        # Verify only 2 receipts remain
        remaining_receipts = self.db_manager.get_all_receipts()
        self.assertEqual(len(remaining_receipts), 2)
    
    def test_get_vendor_statistics(self):
        """Test vendor statistics generation."""
        # Add receipts for same vendor
        receipt1 = Receipt(
            vendor="Test Vendor",
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal("25.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="test1.pdf",
            extracted_text="Test receipt 1",
            confidence_score=0.95
        )
        
        receipt2 = Receipt(
            vendor="Test Vendor",
            transaction_date=datetime(2024, 1, 16),
            amount=Decimal("15.50"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="test2.pdf",
            extracted_text="Test receipt 2",
            confidence_score=0.90
        )
        
        self.db_manager.add_receipt(receipt1)
        self.db_manager.add_receipt(receipt2)
        
        # Get vendor statistics
        vendor_stats = self.db_manager.get_vendor_statistics()
        
        # Verify statistics
        self.assertEqual(len(vendor_stats), 1)
        vendor_name, count, total = vendor_stats[0]
        self.assertEqual(vendor_name, "Test Vendor")
        self.assertEqual(count, 2)
        self.assertEqual(total, Decimal("41.49"))
    
    def test_get_database_statistics(self):
        """Test database statistics generation."""
        # Add some test data
        receipt1 = Receipt(
            vendor="Store A",
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal("25.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="store_a.pdf",
            extracted_text="Store A receipt",
            confidence_score=0.95
        )
        
        receipt2 = Receipt(
            vendor="Store B",
            transaction_date=datetime(2024, 1, 20),
            amount=Decimal("35.50"),
            category=CategoryEnum.RESTAURANTS,
            currency=CurrencyEnum.EUR,
            source_file="store_b.pdf",
            extracted_text="Store B receipt",
            confidence_score=0.90
        )
        
        self.db_manager.add_receipt(receipt1)
        self.db_manager.add_receipt(receipt2)
        
        # Get database statistics
        stats = self.db_manager.get_database_statistics()
        
        # Verify statistics
        self.assertEqual(stats['total_receipts'], 2)
        self.assertEqual(stats['total_amount'], Decimal("61.49"))
        self.assertEqual(stats['unique_vendors'], 2)
        self.assertEqual(stats['unique_categories'], 2)
        self.assertEqual(stats['unique_currencies'], 2)
        self.assertIsNotNone(stats['date_range']['earliest'])
        self.assertIsNotNone(stats['date_range']['latest'])

if __name__ == '__main__':
    unittest.main()
