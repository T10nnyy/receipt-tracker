"""
Unit tests for data models.
Tests Pydantic model validation and business logic.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.core.models import Receipt, SearchFilters, CategoryEnum, CurrencyEnum


class TestReceiptModel:
    """Test Receipt model validation and functionality."""
    
    def test_valid_receipt_creation(self):
        """Test creating a valid receipt."""
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date.today(),
            amount=Decimal("25.99"),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            source_file="test.pdf"
        )
        
        assert receipt.vendor == "Test Store"
        assert receipt.amount == Decimal("25.99")
        assert receipt.category == CategoryEnum.GROCERIES
        assert receipt.currency == CurrencyEnum.USD
    
    def test_vendor_validation(self):
        """Test vendor name validation."""
        # Test empty vendor
        with pytest.raises(ValueError):
            Receipt(
                vendor="",
                transaction_date=date.today(),
                amount=Decimal("25.99"),
                source_file="test.pdf"
            )
        
        # Test vendor cleaning
        receipt = Receipt(
            vendor="  Test   Store  ",
            transaction_date=date.today(),
            amount=Decimal("25.99"),
            source_file="test.pdf"
        )
        assert receipt.vendor == "Test Store"
    
    def test_amount_validation(self):
        """Test amount validation."""
        # Test negative amount
        with pytest.raises(ValueError):
            Receipt(
                vendor="Test Store",
                transaction_date=date.today(),
                amount=Decimal("-5.00"),
                source_file="test.pdf"
            )
        
        # Test zero amount
        with pytest.raises(ValueError):
            Receipt(
                vendor="Test Store",
                transaction_date=date.today(),
                amount=Decimal("0.00"),
                source_file="test.pdf"
            )
        
        # Test valid amount
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date.today(),
            amount=Decimal("0.01"),
            source_file="test.pdf"
        )
        assert receipt.amount == Decimal("0.01")
    
    def test_date_validation(self):
        """Test transaction date validation."""
        from datetime import timedelta
        
        # Test future date
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValueError):
            Receipt(
                vendor="Test Store",
                transaction_date=future_date,
                amount=Decimal("25.99"),
                source_file="test.pdf"
            )
        
        # Test valid date
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date.today(),
            amount=Decimal("25.99"),
            source_file="test.pdf"
        )
        assert receipt.transaction_date == date.today()


class TestSearchFilters:
    """Test SearchFilters model validation."""
    
    def test_valid_filters(self):
        """Test creating valid search filters."""
        filters = SearchFilters(
            vendor_query="Test Store",
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31),
            amount_min=Decimal("10.00"),
            amount_max=Decimal("100.00"),
            category=CategoryEnum.GROCERIES
        )
        
        assert filters.vendor_query == "Test Store"
        assert filters.date_from == date(2024, 1, 1)
        assert filters.amount_min == Decimal("10.00")
    
    def test_date_range_validation(self):
        """Test date range validation."""
        # Test invalid date range
        with pytest.raises(ValueError):
            SearchFilters(
                date_from=date(2024, 12, 31),
                date_to=date(2024, 1, 1)
            )
    
    def test_amount_range_validation(self):
        """Test amount range validation."""
        # Test invalid amount range
        with pytest.raises(ValueError):
            SearchFilters(
                amount_min=Decimal("100.00"),
                amount_max=Decimal("10.00")
            )


if __name__ == "__main__":
    pytest.main([__file__])
