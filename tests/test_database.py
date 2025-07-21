import unittest
import tempfile
import os
from datetime import datetime
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.database import ReceiptDatabase
from core.models import Receipt, ReceiptItem

class TestReceiptDatabase(unittest.TestCase):
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = ReceiptDatabase(self.temp_db.name)
        
        # Create test receipt
        self.test_receipt = Receipt(
            store_name="Test Store",
            date=datetime.now(),
            total=25.99,
            items=[
                ReceiptItem(name="Test Item 1", price=10.99, quantity=1),
                ReceiptItem(name="Test Item 2", price=15.00, quantity=1)
            ],
            category="Grocery"
        )
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_add_receipt(self):
        """Test adding a receipt"""
        receipt_id = self.db.add_receipt(self.test_receipt)
        self.assertIsInstance(receipt_id, int)
        self.assertGreater(receipt_id, 0)
    
    def test_get_receipt(self):
        """Test retrieving a receipt"""
        receipt_id = self.db.add_receipt(self.test_receipt)
        retrieved_receipt = self.db.get_receipt(receipt_id)
        
        self.assertIsNotNone(retrieved_receipt)
        self.assertEqual(retrieved_receipt.store_name, self.test_receipt.store_name)
        self.assertEqual(retrieved_receipt.total, self.test_receipt.total)
        self.assertEqual(len(retrieved_receipt.items), len(self.test_receipt.items))
    
    def test_get_all_receipts(self):
        """Test getting all receipts"""
        # Add multiple receipts
        self.db.add_receipt(self.test_receipt)
        
        receipt2 = Receipt(
            store_name="Another Store",
            date=datetime.now(),
            total=15.50,
            items=[ReceiptItem(name="Item", price=15.50, quantity=1)],
            category="Restaurant"
        )
        self.db.add_receipt(receipt2)
        
        all_receipts = self.db.get_all_receipts()
        self.assertEqual(len(all_receipts), 2)
    
    def test_update_receipt(self):
        """Test updating a receipt"""
        receipt_id = self.db.add_receipt(self.test_receipt)
        
        # Update the receipt
        self.test_receipt.receipt_id = receipt_id
        self.test_receipt.total = 30.00
        self.test_receipt.store_name = "Updated Store"
        
        success = self.db.update_receipt(self.test_receipt)
        self.assertTrue(success)
        
        # Verify update
        updated_receipt = self.db.get_receipt(receipt_id)
        self.assertEqual(updated_receipt.total, 30.00)
        self.assertEqual(updated_receipt.store_name, "Updated Store")
    
    def test_delete_receipt(self):
        """Test deleting a receipt"""
        receipt_id = self.db.add_receipt(self.test_receipt)
        
        success = self.db.delete_receipt(receipt_id)
        self.assertTrue(success)
        
        # Verify deletion
        deleted_receipt = self.db.get_receipt(receipt_id)
        self.assertIsNone(deleted_receipt)
    
    def test_get_statistics(self):
        """Test getting statistics"""
        self.db.add_receipt(self.test_receipt)
        
        stats = self.db.get_statistics()
        self.assertEqual(stats.total_receipts, 1)
        self.assertEqual(stats.total_spent, self.test_receipt.total)
        self.assertEqual(stats.average_receipt, self.test_receipt.total)
    
    def test_search_receipts(self):
        """Test searching receipts"""
        self.db.add_receipt(self.test_receipt)
        
        # Search by store name
        results = self.db.search_receipts("Test Store")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].store_name, "Test Store")
        
        # Search by item name
        results = self.db.search_receipts("Test Item")
        self.assertEqual(len(results), 1)
    
    def test_get_spending_by_category(self):
        """Test getting spending by category"""
        self.db.add_receipt(self.test_receipt)
        
        category_spending = self.db.get_spending_by_category()
        self.assertEqual(len(category_spending), 1)
        self.assertEqual(category_spending[0]['category'], 'Grocery')
        self.assertEqual(category_spending[0]['total'], self.test_receipt.total)

if __name__ == '__main__':
    unittest.main()
