import unittest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from src.core.database import DatabaseManager
from src.core.models import Receipt, ReceiptItem

class TestDatabaseManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_receipts.db")
        self.db_manager = DatabaseManager(self.db_path)
        
        # Create test receipt
        self.test_receipt = Receipt(
            filename="test_receipt.jpg",
            raw_text="Test Store\nItem 1 $5.99\nItem 2 $3.50\nTotal: $9.49",
            upload_date=datetime.now(),
            merchant_name="Test Store",
            receipt_date=datetime(2024, 1, 15),
            total_amount=9.49,
            items=[
                ReceiptItem(name="Item 1", price=5.99, quantity=1),
                ReceiptItem(name="Item 2", price=3.50, quantity=1)
            ]
        )
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database initialization"""
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_save_receipt(self):
        """Test saving a receipt"""
        receipt_id = self.db_manager.save_receipt(self.test_receipt)
        self.assertIsNotNone(receipt_id)
        self.assertEqual(receipt_id, self.test_receipt.id)
    
    def test_get_receipt(self):
        """Test retrieving a receipt"""
        # Save receipt first
        self.db_manager.save_receipt(self.test_receipt)
        
        # Retrieve receipt
        retrieved_receipt = self.db_manager.get_receipt(self.test_receipt.id)
        
        self.assertIsNotNone(retrieved_receipt)
        self.assertEqual(retrieved_receipt.filename, self.test_receipt.filename)
        self.assertEqual(retrieved_receipt.merchant_name, self.test_receipt.merchant_name)
        self.assertEqual(retrieved_receipt.total_amount, self.test_receipt.total_amount)
        self.assertEqual(len(retrieved_receipt.items), len(self.test_receipt.items))
    
    def test_get_all_receipts(self):
        """Test retrieving all receipts"""
        # Save multiple receipts
        receipt2 = Receipt(
            filename="test_receipt2.jpg",
            raw_text="Another Store\nItem 3 $12.99\nTotal: $12.99",
            upload_date=datetime.now(),
            merchant_name="Another Store",
            total_amount=12.99
        )
        
        self.db_manager.save_receipt(self.test_receipt)
        self.db_manager.save_receipt(receipt2)
        
        # Retrieve all receipts
        all_receipts = self.db_manager.get_all_receipts()
        
        self.assertEqual(len(all_receipts), 2)
    
    def test_delete_receipt(self):
        """Test deleting a receipt"""
        # Save receipt first
        self.db_manager.save_receipt(self.test_receipt)
        
        # Delete receipt
        success = self.db_manager.delete_receipt(self.test_receipt.id)
        self.assertTrue(success)
        
        # Verify deletion
        retrieved_receipt = self.db_manager.get_receipt(self.test_receipt.id)
        self.assertIsNone(retrieved_receipt)
    
    def test_search_receipts(self):
        """Test searching receipts"""
        # Save receipt
        self.db_manager.save_receipt(self.test_receipt)
        
        # Search by merchant name
        results = self.db_manager.search_receipts("Test Store")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].merchant_name, "Test Store")
        
        # Search by item
        results = self.db_manager.search_receipts("Item 1")
        self.assertEqual(len(results), 1)
        
        # Search with no results
        results = self.db_manager.search_receipts("Nonexistent")
        self.assertEqual(len(results), 0)
    
    def test_get_analytics_data(self):
        """Test getting analytics data"""
        # Save receipt
        self.db_manager.save_receipt(self.test_receipt)
        
        # Get analytics
        analytics = self.db_manager.get_analytics_data()
        
        self.assertEqual(analytics['total_receipts'], 1)
        self.assertEqual(analytics['total_amount'], 9.49)
        self.assertEqual(analytics['unique_merchants'], 1)
    
    def test_receipt_with_no_items(self):
        """Test saving receipt with no items"""
        receipt_no_items = Receipt(
            filename="no_items.jpg",
            raw_text="Simple receipt with no items parsed",
            upload_date=datetime.now(),
            merchant_name="Simple Store",
            total_amount=5.00
        )
        
        receipt_id = self.db_manager.save_receipt(receipt_no_items)
        self.assertIsNotNone(receipt_id)
        
        retrieved = self.db_manager.get_receipt(receipt_id)
        self.assertEqual(len(retrieved.items), 0)
    
    def test_update_receipt(self):
        """Test updating an existing receipt"""
        # Save original receipt
        self.db_manager.save_receipt(self.test_receipt)
        
        # Modify receipt
        self.test_receipt.merchant_name = "Updated Store Name"
        self.test_receipt.total_amount = 15.99
        
        # Save updated receipt
        self.db_manager.save_receipt(self.test_receipt)
        
        # Retrieve and verify update
        retrieved = self.db_manager.get_receipt(self.test_receipt.id)
        self.assertEqual(retrieved.merchant_name, "Updated Store Name")
        self.assertEqual(retrieved.total_amount, 15.99)

if __name__ == '__main__':
    unittest.main()
