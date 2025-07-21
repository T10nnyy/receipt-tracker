"""
Unit tests for database operations.
Tests CRUD operations and data integrity.
"""

import pytest
import tempfile
import os
from datetime import date, datetime
from decimal import Decimal

from src.core.database import ReceiptDatabase, DatabaseError
from src.core.models import Receipt, SearchFilters, CategoryEnum, CurrencyEnum


class TestReceiptDatabase:
    """Test database operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        db = ReceiptDatabase(temp_file.name)
        yield db
        
        # Cleanup
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def sample_receipt(self):
        """Create sample receipt for testing."""
        return Receipt(
            vendor="Test Store",
            transaction_date=date.today(),
            amount=Decimal("25.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="test.pdf",
            extracted_text="Test receipt text",
            confidence_score=95.0
        )
    
    def test_add_receipt(self, temp_db, sample_receipt):
        """Test adding a receipt to database."""
        receipt_id = temp_db.add_receipt(sample_receipt)
        
        assert receipt_id is not None
        assert receipt_id > 0
        
        # Verify receipt was added
        retrieved = temp_db.get_receipt(receipt_id)
        assert retrieved is not None
        assert retrieved.vendor == sample_receipt.vendor
        assert retrieved.amount == sample_receipt.amount
    
    def test_get_receipt(self, temp_db, sample_receipt):
        """Test retrieving a receipt by ID."""
        receipt_id = temp_db.add_receipt(sample_receipt)
        
        retrieved = temp_db.get_receipt(receipt_id)
        assert retrieved is not None
        assert retrieved.id == receipt_id
        assert retrieved.vendor == sample_receipt.vendor
        
        # Test non-existent receipt
        non_existent = temp_db.get_receipt(99999)
        assert non_existent is None
    
    def test_update_receipt(self, temp_db, sample_receipt):
        """Test updating a receipt."""
        receipt_id = temp_db.add_receipt(sample_receipt)
        
        # Update receipt
        sample_receipt.id = receipt_id
        sample_receipt.vendor = "Updated Store"
        sample_receipt.amount = Decimal("30.00")
        
        success = temp_db.update_receipt(sample_receipt)
        assert success is True
        
        # Verify update
        updated = temp_db.get_receipt(receipt_id)
        assert updated.vendor == "Updated Store"
        assert updated.amount == Decimal("30.00")
    
    def test_delete_receipt(self, temp_db, sample_receipt):
        """Test deleting a receipt."""
        receipt_id = temp_db.add_receipt(sample_receipt)
        
        # Verify receipt exists
        assert temp_db.get_receipt(receipt_id) is not None
        
        # Delete receipt
        success = temp_db.delete_receipt(receipt_id)
        assert success is True
        
        # Verify deletion
        assert temp_db.get_receipt(receipt_id) is None
        
        # Test deleting non-existent receipt
        success = temp_db.delete_receipt(99999)
        assert success is False
    
    def test_search_receipts(self, temp_db):
        """Test searching receipts with filters."""
        # Add test receipts
        receipts = [
            Receipt(
                vendor="Store A",
                transaction_date=date(2024, 1, 15),
                amount=Decimal("25.99"),
                category=CategoryEnum.GROCERIES,
                source_file="test1.pdf"
            ),
            Receipt(
                vendor="Store B",
                transaction_date=date(2024, 2, 20),
                amount=Decimal("45.50"),
                category=CategoryEnum.FOOD,
                source_file="test2.pdf"
            ),
            Receipt(
                vendor="Store A",
                transaction_date=date(2024, 3, 10),
                amount=Decimal("15.75"),
                category=CategoryEnum.GROCERIES,
                source_file="test3.pdf"
            )
        ]
        
        for receipt in receipts:
            temp_db.add_receipt(receipt)
        
        # Test vendor search
        filters = SearchFilters(vendor_query="Store A")
        results = temp_db.search_receipts(filters)
        assert len(results) == 2
        assert all(r.vendor == "Store A" for r in results)
        
        # Test date range search
        filters = SearchFilters(
            date_from=date(2024, 2, 1),
            date_to=date(2024, 2, 28)
        )
        results = temp_db.search_receipts(filters)
        assert len(results) == 1
        assert results[0].vendor == "Store B"
        
        # Test amount range search
        filters = SearchFilters(
            amount_min=Decimal("20.00"),
            amount_max=Decimal("50.00")
        )
        results = temp_db.search_receipts(filters)
        assert len(results) == 2
        
        # Test category search
        filters = SearchFilters(category=CategoryEnum.GROCERIES)
        results = temp_db.search_receipts(filters)
        assert len(results) == 2
        assert all(r.category == CategoryEnum.GROCERIES for r in results)
    
    def test_get_analytics(self, temp_db):
        """Test analytics generation."""
        # Add test receipts
        receipts = [
            Receipt(
                vendor="Store A",
                transaction_date=date(2024, 1, 15),
                amount=Decimal("25.99"),
                category=CategoryEnum.GROCERIES,
                source_file="test1.pdf"
            ),
            Receipt(
                vendor="Store B",
                transaction_date=date(2024, 1, 20),
                amount=Decimal("45.50"),
                category=CategoryEnum.FOOD,
                source_file="test2.pdf"
            )
        ]
        
        for receipt in receipts:
            temp_db.add_receipt(receipt)
        
        analytics = temp_db.get_analytics()
        
        assert analytics.total_receipts == 2
        assert analytics.total_amount == Decimal("71.49")
        assert analytics.average_amount == Decimal("35.745")
        assert len(analytics.top_vendors) == 2
        assert len(analytics.category_breakdown) == 2


if __name__ == "__main__":
    pytest.main([__file__])
