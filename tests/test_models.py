"""
Models Module Tests - Data Validation Test Suite

This module contains comprehensive unit tests for the Pydantic data models
including validation rules, type checking, and data integrity constraints.

Author: Receipt Processing Team
Version: 1.0.0
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import pytest
from pydantic import ValidationError

# Import modules to test
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.models import (
    Receipt, CategoryEnum, CurrencyEnum, ProcessingResult, 
    SearchFilters, AnalyticsData, FileUploadData,
    classify_category, detect_currency
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
        receipt = Receipt(**self.valid_receipt_data)
        
        self.assertEqual(receipt.vendor, 'Test Vendor')
        self.assertEqual(receipt.amount, Decimal('25.99'))
        self.assertEqual(receipt.category, CategoryEnum.GROCERIES)
        self.assertEqual(receipt.currency, CurrencyEnum.USD)
        self.assertEqual(receipt.confidence_score, 0.95)
    
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

if __name__ == '__main__':
    unittest.main()
