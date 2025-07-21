"""
Models Module Tests - Data Validation Test Suite

This module contains comprehensive unit tests for the Pydantic data models
including validation rules, type checking, and data integrity constraints.

Author: Receipt Processing Team
Version: 1.0.0
"""

import unittest
from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path
import pytest
from pydantic import ValidationError

# Import modules to test
import sys
import os

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.models import (
    Receipt, CategoryEnum, CurrencyEnum, ProcessingResult, 
    SearchFilters, AnalyticsData, FileUploadData, ReceiptSearchFilter,
    classify_category, detect_currency, ReceiptItem, ReceiptStatistics
)

class TestReceiptModel(unittest.TestCase):
    """Test suite for Receipt model validation."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_receipt_data = {
            'vendor': 'Test Vendor',
            'transaction_date': datetime(2024, 1, 15, 10, 30),
            'amount': Decimal('25.99'),
            'category': CategoryEnum.GROCERIES,
            'currency': CurrencyEnum.USD,
            'source_file': 'test_receipt.pdf',
            'extracted_text': 'Test receipt content',
            'confidence_score': 0.95
        }
    
    def test_valid_receipt_creation(self):
        """Test creating a valid receipt."""
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            items=["Item 1", "Item 2"],
            category="Groceries",
            payment_method="Credit Card"
        )
        
        self.assertEqual(receipt.vendor, "Test Store")
        self.assertEqual(receipt.amount, 25.50)
        self.assertEqual(receipt.category, "Groceries")
        self.assertEqual(len(receipt.items), 2)
    
    def test_receipt_with_defaults(self):
        """Test receipt creation with default values."""
        minimal_data = {
            'vendor': 'Test Vendor',
            'transaction_date': datetime(2024, 1, 15),
            'amount': Decimal('25.99'),
            'source_file': 'test.pdf'
        }
        
        receipt = Receipt(**minimal_data)
        
        # Check defaults
        self.assertEqual(receipt.category, CategoryEnum.OTHER)
        self.assertEqual(receipt.currency, CurrencyEnum.USD)
        self.assertEqual(receipt.confidence_score, 0.0)
        self.assertIsNone(receipt.extracted_text)
    
    def test_invalid_vendor_empty(self):
        """Test validation fails for empty vendor."""
        data = self.valid_receipt_data.copy()
        data['vendor'] = ''
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_vendor_too_long(self):
        """Test validation fails for vendor name too long."""
        data = self.valid_receipt_data.copy()
        data['vendor'] = 'A' * 201  # Exceeds 200 character limit
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_amount_negative(self):
        """Test validation fails for negative amount."""
        data = self.valid_receipt_data.copy()
        data['amount'] = Decimal('-10.00')
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_amount_zero(self):
        """Test validation fails for zero amount."""
        data = self.valid_receipt_data.copy()
        data['amount'] = Decimal('0.00')
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_future_date(self):
        """Test validation fails for future transaction date."""
        data = self.valid_receipt_data.copy()
        data['transaction_date'] = datetime.now() + timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_old_date(self):
        """Test validation fails for very old transaction date."""
        data = self.valid_receipt_data.copy()
        data['transaction_date'] = datetime(1990, 1, 1)  # More than 10 years ago
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_confidence_score_negative(self):
        """Test validation fails for negative confidence score."""
        data = self.valid_receipt_data.copy()
        data['confidence_score'] = -0.1
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_confidence_score_too_high(self):
        """Test validation fails for confidence score > 1."""
        data = self.valid_receipt_data.copy()
        data['confidence_score'] = 1.1
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_invalid_source_file_extension(self):
        """Test validation fails for invalid file extension."""
        data = self.valid_receipt_data.copy()
        data['source_file'] = 'test.xyz'  # Invalid extension
        
        with self.assertRaises(ValidationError):
            Receipt(**data)
    
    def test_vendor_name_cleaning(self):
        """Test vendor name is properly cleaned."""
        data = self.valid_receipt_data.copy()
        data['vendor'] = '  Test   Vendor  '  # Extra whitespace
        
        receipt = Receipt(**data)
        self.assertEqual(receipt.vendor, 'Test Vendor')
    
    def test_amount_precision(self):
        """Test amount is properly quantized to 2 decimal places."""
        data = self.valid_receipt_data.copy()
        data['amount'] = Decimal('25.999')  # 3 decimal places
        
        receipt = Receipt(**data)
        self.assertEqual(receipt.amount, Decimal('26.00'))  # Rounded to 2 places
    
    def test_confidence_score_rounding(self):
        """Test confidence score is rounded to 3 decimal places."""
        data = self.valid_receipt_data.copy()
        data['confidence_score'] = 0.123456789
        
        receipt = Receipt(**data)
        self.assertEqual(receipt.confidence_score, 0.123)
    
    def test_to_dict_conversion(self):
        """Test receipt conversion to dictionary."""
        receipt = Receipt(**self.valid_receipt_data)
        receipt_dict = receipt.to_dict()
        
        self.assertIsInstance(receipt_dict, dict)
        self.assertEqual(receipt_dict['vendor'], 'Test Vendor')
        self.assertEqual(receipt_dict['amount'], '25.99')
        self.assertEqual(receipt_dict['category'], 'groceries')
        self.assertEqual(receipt_dict['currency'], 'USD')
        self.assertIn('transaction_date', receipt_dict)
    
    def test_from_dict_creation(self):
        """Test receipt creation from dictionary."""
        receipt_dict = {
            'vendor': 'Test Vendor',
            'transaction_date': '2024-01-15T10:30:00',
            'amount': '25.99',
            'category': 'groceries',
            'currency': 'USD',
            'source_file': 'test.pdf',
            'confidence_score': 0.95
        }
        
        receipt = Receipt.from_dict(receipt_dict)
        
        self.assertEqual(receipt.vendor, 'Test Vendor')
        self.assertEqual(receipt.amount, Decimal('25.99'))
        self.assertEqual(receipt.category, CategoryEnum.GROCERIES)
        self.assertIsInstance(receipt.transaction_date, datetime)
    
    def test_vendor_validation(self):
        """Test vendor name validation."""
        # Test empty vendor
        with self.assertRaises(ValidationError):
            Receipt(
                vendor="",
                transaction_date=date(2023, 1, 15),
                amount=25.50
            )
        
        # Test whitespace-only vendor
        with self.assertRaises(ValidationError):
            Receipt(
                vendor="   ",
                transaction_date=date(2023, 1, 15),
                amount=25.50
            )
        
        # Test vendor name cleaning
        receipt = Receipt(
            vendor="  test store  ",
            transaction_date=date(2023, 1, 15),
            amount=25.50
        )
        self.assertEqual(receipt.vendor, "Test Store")
    
    def test_amount_validation(self):
        """Test amount validation."""
        # Test negative amount
        with self.assertRaises(ValidationError):
            Receipt(
                vendor="Test Store",
                transaction_date=date(2023, 1, 15),
                amount=-5.00
            )
        
        # Test zero amount
        with self.assertRaises(ValidationError):
            Receipt(
                vendor="Test Store",
                transaction_date=date(2023, 1, 15),
                amount=0.00
            )
        
        # Test very large amount
        with self.assertRaises(ValidationError):
            Receipt(
                vendor="Test Store",
                transaction_date=date(2023, 1, 15),
                amount=150000.00
            )
        
        # Test amount rounding
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.555
        )
        self.assertEqual(receipt.amount, 25.56)
    
    def test_category_validation(self):
        """Test category validation."""
        # Test valid category
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            category="Food & Dining"
        )
        self.assertEqual(receipt.category, "Food & Dining")
        
        # Test invalid category (should default to "Other")
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            category="Invalid Category"
        )
        self.assertEqual(receipt.category, "Other")
    
    def test_payment_method_validation(self):
        """Test payment method validation."""
        # Test valid payment method
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            payment_method="Credit Card"
        )
        self.assertEqual(receipt.payment_method, "Credit Card")
        
        # Test invalid payment method (should default to "Unknown")
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            payment_method="Invalid Method"
        )
        self.assertEqual(receipt.payment_method, "Unknown")
    
    def test_items_validation(self):
        """Test items list validation."""
        # Test empty items
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            items=[]
        )
        self.assertEqual(receipt.items, [])
        
        # Test items cleaning (remove empty strings)
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            items=["Item 1", "", "  ", "Item 2", "Item 3"]
        )
        self.assertEqual(receipt.items, ["Item 1", "Item 2", "Item 3"])
        
        # Test items limit (should limit to 50 items)
        many_items = [f"Item {i}" for i in range(100)]
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            items=many_items
        )
        self.assertEqual(len(receipt.items), 50)
    
    def test_to_dict(self):
        """Test converting receipt to dictionary."""
        receipt = Receipt(
            vendor="Test Store",
            transaction_date=date(2023, 1, 15),
            amount=25.50,
            items=["Item 1", "Item 2"],
            category="Groceries",
            payment_method="Credit Card"
        )
        
        receipt_dict = receipt.to_dict()
        
        self.assertIsInstance(receipt_dict, dict)
        self.assertEqual(receipt_dict['vendor'], "Test Store")
        self.assertEqual(receipt_dict['amount'], 25.50)
        self.assertEqual(receipt_dict['transaction_date'], "2023-01-15")
        self.assertEqual(receipt_dict['items'], ["Item 1", "Item 2"])
    
    def test_from_dict(self):
        """Test creating receipt from dictionary."""
        receipt_data = {
            'vendor': "Test Store",
            'transaction_date': "2023-01-15",
            'amount': 25.50,
            'items': ["Item 1", "Item 2"],
            'category': "Groceries",
            'payment_method': "Credit Card"
        }
        
        receipt = Receipt.from_dict(receipt_data)
        
        self.assertEqual(receipt.vendor, "Test Store")
        self.assertEqual(receipt.amount, 25.50)
        self.assertEqual(receipt.transaction_date, date(2023, 1, 15))
        self.assertEqual(receipt.items, ["Item 1", "Item 2"])

class TestSearchFilters(unittest.TestCase):
    """Test suite for SearchFilters model."""
    
    def test_valid_search_filters(self):
        """Test creating valid search filters."""
        filters = SearchFilters(
            vendor_query='Test Vendor',
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 31),
            amount_min=Decimal('10.00'),
            amount_max=Decimal('100.00'),
            category=CategoryEnum.GROCERIES,
            currency=CurrencyEnum.USD,
            confidence_threshold=0.5,
            fuzzy_search=True
        )
        
        self.assertEqual(filters.vendor_query, 'Test Vendor')
        self.assertEqual(filters.amount_min, Decimal('10.00'))
        self.assertTrue(filters.fuzzy_search)
    
    def test_invalid_date_range(self):
        """Test validation fails when end date is before start date."""
        with self.assertRaises(ValidationError):
            SearchFilters(
                date_from=datetime(2024, 1, 31),
                date_to=datetime(2024, 1, 1)  # End before start
            )
    
    def test_invalid_amount_range(self):
        """Test validation fails when max amount is less than min amount."""
        with self.assertRaises(ValidationError):
            SearchFilters(
                amount_min=Decimal('100.00'),
                amount_max=Decimal('50.00')  # Max less than min
            )
    
    def test_search_filters_defaults(self):
        """Test search filters with default values."""
        filters = SearchFilters()
        
        self.assertIsNone(filters.vendor_query)
        self.assertIsNone(filters.date_from)
        self.assertEqual(filters.confidence_threshold, 0.0)
        self.assertFalse(filters.fuzzy_search)

class TestProcessingResult(unittest.TestCase):
    """Test suite for ProcessingResult model."""
    
    def test_successful_processing_result(self):
        """Test creating a successful processing result."""
        receipt = Receipt(
            vendor='Test Vendor',
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal('25.99'),
            source_file='test.pdf'
        )
        
        result = ProcessingResult(
            success=True,
            receipt=receipt,
            processing_time=1.5,
            warnings=['Minor OCR issue']
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.receipt)
        self.assertEqual(result.processing_time, 1.5)
        self.assertEqual(len(result.warnings), 1)
    
    def test_failed_processing_result(self):
        """Test creating a failed processing result."""
        result = ProcessingResult(
            success=False,
            error_message='File could not be processed'
        )
        
        self.assertFalse(result.success)
        self.assertIsNone(result.receipt)
        self.assertEqual(result.error_message, 'File could not be processed')

class TestFileUploadData(unittest.TestCase):
    """Test suite for FileUploadData model."""
    
    def test_valid_file_upload_data(self):
        """Test creating valid file upload data."""
        upload_data = FileUploadData(
            filename='test_receipt.pdf',
            file_size=1024000,  # 1MB
            file_type='application/pdf'
        )
        
        self.assertEqual(upload_data.filename, 'test_receipt.pdf')
        self.assertEqual(upload_data.file_size, 1024000)
        self.assertEqual(upload_data.file_type, 'application/pdf')
        self.assertIsInstance(upload_data.upload_timestamp, datetime)
    
    def test_invalid_file_size_too_large(self):
        """Test validation fails for file size too large."""
        with self.assertRaises(ValidationError):
            FileUploadData(
                filename='large_file.pdf',
                file_size=11 * 1024 * 1024,  # 11MB (exceeds 10MB limit)
                file_type='application/pdf'
            )
    
    def test_invalid_file_type(self):
        """Test validation fails for unsupported file type."""
        with self.assertRaises(ValidationError):
            FileUploadData(
                filename='test.xyz',
                file_size=1024,
                file_type='application/xyz'  # Unsupported type
            )

class TestCategoryClassification(unittest.TestCase):
    """Test suite for category classification function."""
    
    def test_classify_grocery_category(self):
        """Test classification of grocery receipts."""
        text = "WALMART SUPERCENTER Receipt Total: $25.99 Food items"
        vendor = "Walmart"
        
        category = classify_category(text, vendor)
        self.assertEqual(category, CategoryEnum.GROCERIES)
    
    def test_classify_restaurant_category(self):
        """Test classification of restaurant receipts."""
        text = "McDonald's Restaurant Order #123 Burger and fries"
        vendor = "McDonald's"
        
        category = classify_category(text, vendor)
        self.assertEqual(category, CategoryEnum.RESTAURANTS)
    
    def test_classify_gas_station_category(self):
        """Test classification of gas station receipts."""
        text = "Shell Gas Station Fuel purchase Gallons: 10.5"
        vendor = "Shell"
        
        category = classify_category(text, vendor)
        self.assertEqual(category, CategoryEnum.TRANSPORTATION)
    
    def test_classify_unknown_category(self):
        """Test classification defaults to OTHER for unknown receipts."""
        text = "Unknown business receipt with no clear indicators"
        vendor = "Unknown Business"
        
        category = classify_category(text, vendor)
        self.assertEqual(category, CategoryEnum.OTHER)

class TestCurrencyDetection(unittest.TestCase):
    """Test suite for currency detection function."""
    
    def test_detect_usd_currency(self):
        """Test detection of USD currency."""
        text = "Total: $25.99 USD"
        
        currency = detect_currency(text)
        self.assertEqual(currency, CurrencyEnum.USD)
    
    def test_detect_eur_currency(self):
        """Test detection of EUR currency."""
        text = "Total: €25.99 EUR"
        
        currency = detect_currency(text)
        self.assertEqual(currency, CurrencyEnum.EUR)
    
    def test_detect_gbp_currency(self):
        """Test detection of GBP currency."""
        text = "Total: £25.99 GBP"
        
        currency = detect_currency(text)
        self.assertEqual(currency, CurrencyEnum.GBP)
    
    def test_detect_default_currency(self):
        """Test detection defaults to USD for unknown currency."""
        text = "Total: 25.99 (no currency symbol)"
        
        currency = detect_currency(text)
        self.assertEqual(currency, CurrencyEnum.USD)

class TestEnumValues(unittest.TestCase):
    """Test suite for enum definitions."""
    
    def test_category_enum_values(self):
        """Test CategoryEnum has expected values."""
        expected_categories = {
            'groceries', 'restaurants', 'utilities', 'transportation',
            'healthcare', 'entertainment', 'shopping', 'services',
            'education', 'travel', 'other'
        }
        
        actual_categories = {cat.value for cat in CategoryEnum}
        self.assertEqual(actual_categories, expected_categories)
    
    def test_currency_enum_values(self):
        """Test CurrencyEnum has expected values."""
        expected_currencies = {
            'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'CNY'
        }
        
        actual_currencies = {curr.value for curr in CurrencyEnum}
        self.assertEqual(actual_currencies, expected_currencies)

class TestReceiptSearchFilter(unittest.TestCase):
    """Test cases for ReceiptSearchFilter model."""
    
    def test_valid_search_filter(self):
        """Test creating a valid search filter."""
        search_filter = ReceiptSearchFilter(
            query="test",
            vendor="Test Store",
            category="Groceries",
            min_amount=10.0,
            max_amount=50.0,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        self.assertEqual(search_filter.query, "test")
        self.assertEqual(search_filter.vendor, "Test Store")
        self.assertEqual(search_filter.min_amount, 10.0)
        self.assertEqual(search_filter.max_amount, 50.0)
    
    def test_empty_search_filter(self):
        """Test creating an empty search filter."""
        search_filter = ReceiptSearchFilter()
        
        self.assertIsNone(search_filter.query)
        self.assertIsNone(search_filter.vendor)
        self.assertIsNone(search_filter.min_amount)
        self.assertIsNone(search_filter.max_amount)
    
    def test_amount_validation(self):
        """Test amount validation in search filter."""
        # Test negative amounts
        with self.assertRaises(ValidationError):
            ReceiptSearchFilter(min_amount=-10.0)
        
        with self.assertRaises(ValidationError):
            ReceiptSearchFilter(max_amount=-5.0)
    
    def test_date_range_validation(self):
        """Test date range validation."""
        # Test invalid date range (end before start)
        with self.assertRaises(ValidationError):
            ReceiptSearchFilter(
                start_date=date(2023, 12, 31),
                end_date=date(2023, 1, 1)
            )
        
        # Test valid date range
        search_filter = ReceiptSearchFilter(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        self.assertEqual(search_filter.start_date, date(2023, 1, 1))
        self.assertEqual(search_filter.end_date, date(2023, 12, 31))

class TestReceiptItem(unittest.TestCase):
    
    def test_receipt_item_creation(self):
        """Test creating a receipt item"""
        item = ReceiptItem(
            name="Test Item",
            price=10.99,
            quantity=2,
            category="Food"
        )
        
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.price, 10.99)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.category, "Food")
    
    def test_receipt_item_defaults(self):
        """Test receipt item default values"""
        item = ReceiptItem(name="Test", price=5.00)
        
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.category, "Other")
    
    def test_receipt_item_to_dict(self):
        """Test converting receipt item to dictionary"""
        item = ReceiptItem(name="Test", price=5.00, quantity=2)
        item_dict = item.to_dict()
        
        expected = {
            'name': 'Test',
            'price': 5.00,
            'quantity': 2,
            'category': 'Other'
        }
        
        self.assertEqual(item_dict, expected)
    
    def test_receipt_item_from_dict(self):
        """Test creating receipt item from dictionary"""
        data = {
            'name': 'Test Item',
            'price': 15.99,
            'quantity': 3,
            'category': 'Electronics'
        }
        
        item = ReceiptItem.from_dict(data)
        
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.price, 15.99)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.category, 'Electronics')

class TestReceipt(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.test_items = [
            ReceiptItem(name="Item 1", price=10.00, quantity=1),
            ReceiptItem(name="Item 2", price=15.50, quantity=2)
        ]
        
        self.test_receipt = Receipt(
            store_name="Test Store",
            date=datetime(2024, 1, 15, 14, 30),
            total=41.00,
            items=self.test_items,
            category="Grocery",
            tax=2.50,
            tip=3.00
        )
    
    def test_receipt_creation(self):
        """Test creating a receipt"""
        self.assertEqual(self.test_receipt.store_name, "Test Store")
        self.assertEqual(self.test_receipt.total, 41.00)
        self.assertEqual(len(self.test_receipt.items), 2)
        self.assertEqual(self.test_receipt.category, "Grocery")
    
    def test_receipt_defaults(self):
        """Test receipt default values"""
        receipt = Receipt(
            store_name="Store",
            date=datetime.now(),
            total=10.00
        )
        
        self.assertEqual(receipt.category, "Other")
        self.assertEqual(receipt.tax, 0.0)
        self.assertEqual(receipt.tip, 0.0)
        self.assertEqual(receipt.payment_method, "Unknown")
        self.assertEqual(len(receipt.items), 0)
    
    def test_get_item_count(self):
        """Test getting total item count"""
        count = self.test_receipt.get_item_count()
        self.assertEqual(count, 3)  # 1 + 2 quantities
    
    def test_get_subtotal(self):
        """Test calculating subtotal"""
        subtotal = self.test_receipt.get_subtotal()
        expected = 41.00 - 2.50 - 3.00  # total - tax - tip
        self.assertEqual(subtotal, expected)
    
    def test_add_item(self):
        """Test adding an item to receipt"""
        new_item = ReceiptItem(name="New Item", price=5.00)
        self.test_receipt.add_item(new_item)
        
        self.assertEqual(len(self.test_receipt.items), 3)
        self.assertEqual(self.test_receipt.items[-1].name, "New Item")
    
    def test_remove_item(self):
        """Test removing an item from receipt"""
        self.test_receipt.remove_item(0)
        
        self.assertEqual(len(self.test_receipt.items), 1)
        self.assertEqual(self.test_receipt.items[0].name, "Item 2")
    
    def test_get_items_by_category(self):
        """Test grouping items by category"""
        # Add items with different categories
        self.test_receipt.items[0].category = "Food"
        self.test_receipt.items[1].category = "Beverage"
        
        categories = self.test_receipt.get_items_by_category()
        
        self.assertIn("Food", categories)
        self.assertIn("Beverage", categories)
        self.assertEqual(len(categories["Food"]), 1)
        self.assertEqual(len(categories["Beverage"]), 1)
    
    def test_receipt_to_dict(self):
        """Test converting receipt to dictionary"""
        receipt_dict = self.test_receipt.to_dict()
        
        self.assertEqual(receipt_dict['store_name'], "Test Store")
        self.assertEqual(receipt_dict['total'], 41.00)
        self.assertEqual(len(receipt_dict['items']), 2)
        self.assertIsInstance(receipt_dict['date'], str)
    
    def test_receipt_from_dict(self):
        """Test creating receipt from dictionary"""
        data = {
            'store_name': 'Dict Store',
            'date': '2024-01-15T14:30:00',
            'total': 25.00,
            'items': [
                {'name': 'Dict Item', 'price': 25.00, 'quantity': 1, 'category': 'Other'}
            ],
            'category': 'Test',
            'tax': 1.50,
            'tip': 2.00
        }
        
        receipt = Receipt.from_dict(data)
        
        self.assertEqual(receipt.store_name, 'Dict Store')
        self.assertEqual(receipt.total, 25.00)
        self.assertEqual(len(receipt.items), 1)
        self.assertEqual(receipt.items[0].name, 'Dict Item')

class TestReceiptStatistics(unittest.TestCase):
    
    def test_statistics_creation(self):
        """Test creating receipt statistics"""
        stats = ReceiptStatistics(
            total_receipts=10,
            total_spent=250.00,
            average_receipt=25.00,
            most_frequent_store="Test Store"
        )
        
        self.assertEqual(stats.total_receipts, 10)
        self.assertEqual(stats.total_spent, 250.00)
        self.assertEqual(stats.average_receipt, 25.00)
        self.assertEqual(stats.most_frequent_store, "Test Store")
    
    def test_statistics_defaults(self):
        """Test statistics default values"""
        stats = ReceiptStatistics()
        
        self.assertEqual(stats.total_receipts, 0)
        self.assertEqual(stats.total_spent, 0.0)
        self.assertEqual(stats.average_receipt, 0.0)
        self.assertEqual(stats.most_frequent_store, "")
    
    def test_statistics_to_dict(self):
        """Test converting statistics to dictionary"""
        stats = ReceiptStatistics(total_receipts=5, total_spent=100.00)
        stats_dict = stats.to_dict()
        
        expected_keys = [
            'total_receipts', 'total_spent', 'average_receipt',
            'most_frequent_store', 'most_expensive_receipt',
            'receipts_this_month', 'spending_this_month'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats_dict)

if __name__ == '__main__':
    unittest.main()
