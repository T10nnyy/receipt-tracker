"""
Data Models Module - Pydantic Models for Receipt Processing

This module defines comprehensive data models using Pydantic for formal type checking
and validation. Ensures data integrity throughout the application with proper
validation rules and type safety.

Features:
- Comprehensive field validation
- Type safety with Python type hints
- Automatic data serialization/deserialization
- Custom validators for business logic
- Enum definitions for categorical data

Author: Receipt Processing Team
Version: 1.0.0
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator
import re

class CategoryEnum(str, Enum):
    """Enumeration of receipt categories for classification."""
    GROCERIES = "groceries"
    RESTAURANTS = "restaurants"
    UTILITIES = "utilities"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    SERVICES = "services"
    EDUCATION = "education"
    TRAVEL = "travel"
    OTHER = "other"

class CurrencyEnum(str, Enum):
    """Enumeration of supported currencies."""
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    JPY = "JPY"  # Japanese Yen
    CHF = "CHF"  # Swiss Franc
    CNY = "CNY"  # Chinese Yuan

class Receipt(BaseModel):
    """
    Comprehensive receipt data model with validation.
    
    Represents a processed receipt with all extracted information,
    validation rules, and metadata for tracking and analysis.
    """
    
    id: Optional[int] = Field(None, description="Unique database identifier")
    vendor: str = Field(..., min_length=1, max_length=200, description="Vendor or merchant name")
    transaction_date: datetime = Field(..., description="Date of the transaction")
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="Transaction amount")
    category: CategoryEnum = Field(default=CategoryEnum.OTHER, description="Receipt category")
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD, description="Currency of the transaction")
    source_file: str = Field(..., min_length=1, description="Original file name")
    extracted_text: Optional[str] = Field(None, description="Raw extracted text from OCR")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="OCR confidence score")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }
    
    @validator('vendor')
    def validate_vendor(cls, v):
        """Validate and clean vendor name."""
        if not v or not v.strip():
            raise ValueError("Vendor name cannot be empty")
        
        # Clean and normalize vendor name
        cleaned = re.sub(r'\s+', ' ', v.strip())
        if len(cleaned) > 200:
            raise ValueError("Vendor name too long (max 200 characters)")
        
        return cleaned
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate transaction amount."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        
        # Ensure proper decimal precision
        return v.quantize(Decimal('0.01'))
    
    @validator('transaction_date')
    def validate_transaction_date(cls, v):
        """Validate transaction date."""
        if v > datetime.now():
            raise ValueError("Transaction date cannot be in the future")
        
        # Check if date is too far in the past (more than 10 years)
        min_date = datetime.now().replace(year=datetime.now().year - 10)
        if v < min_date:
            raise ValueError("Transaction date is too far in the past")
        
        return v
    
    @validator('source_file')
    def validate_source_file(cls, v):
        """Validate source file name."""
        if not v or not v.strip():
            raise ValueError("Source file name cannot be empty")
        
        # Check for valid file extensions
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.txt']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Invalid file extension. Supported: {', '.join(valid_extensions)}")
        
        return v.strip()
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Validate OCR confidence score."""
        return round(v, 3)  # Round to 3 decimal places
    
    @root_validator
    def validate_receipt_data(cls, values):
        """Cross-field validation for receipt data."""
        # Ensure high-value transactions have reasonable confidence scores
        amount = values.get('amount')
        confidence = values.get('confidence_score', 0.0)
        
        if amount and amount > Decimal('1000.00') and confidence < 0.5:
            # Don't raise error, but could log warning
            pass
        
        return values
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary for serialization."""
        return {
            'id': self.id,
            'vendor': self.vendor,
            'transaction_date': self.transaction_date.isoformat(),
            'amount': str(self.amount),
            'category': self.category.value,
            'currency': self.currency.value,
            'source_file': self.source_file,
            'extracted_text': self.extracted_text,
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Receipt':
        """Create receipt from dictionary."""
        if 'transaction_date' in data and isinstance(data['transaction_date'], str):
            data['transaction_date'] = datetime.fromisoformat(data['transaction_date'])
        
        if 'amount' in data:
            data['amount'] = Decimal(str(data['amount']))
        
        return cls(**data)

class ProcessingResult(BaseModel):
    """
    Result of receipt processing operation.
    
    Contains the processed receipt data along with metadata about
    the processing operation, including success status and error information.
    """
    
    success: bool = Field(..., description="Whether processing was successful")
    receipt: Optional[Receipt] = Field(None, description="Processed receipt data")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True

class SearchFilters(BaseModel):
    """
    Search filter parameters for receipt queries.
    
    Defines all possible search criteria with proper validation
    for filtering receipt data in the database and analytics.
    """
    
    vendor_query: Optional[str] = Field(None, max_length=200, description="Vendor name search query")
    date_from: Optional[datetime] = Field(None, description="Start date for date range filter")
    date_to: Optional[datetime] = Field(None, description="End date for date range filter")
    amount_min: Optional[Decimal] = Field(None, ge=0, description="Minimum amount filter")
    amount_max: Optional[Decimal] = Field(None, ge=0, description="Maximum amount filter")
    category: Optional[CategoryEnum] = Field(None, description="Category filter")
    currency: Optional[CurrencyEnum] = Field(None, description="Currency filter")
    confidence_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence score")
    fuzzy_search: bool = Field(default=False, description="Enable fuzzy string matching")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        """Validate that date_to is after date_from."""
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError("End date must be after start date")
        return v
    
    @validator('amount_max')
    def validate_amount_range(cls, v, values):
        """Validate that amount_max is greater than amount_min."""
        if v and 'amount_min' in values and values['amount_min']:
            if v < values['amount_min']:
                raise ValueError("Maximum amount must be greater than minimum amount")
        return v

class AnalyticsData(BaseModel):
    """
    Analytics data structure for receipt insights.
    
    Contains comprehensive analytics results including statistical summaries,
    trends, and patterns derived from receipt data analysis.
    """
    
    total_receipts: int = Field(default=0, ge=0, description="Total number of receipts")
    total_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Total spending amount")
    average_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Average transaction amount")
    median_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Median transaction amount")
    vendor_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Vendor statistics")
    category_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Category statistics")
    monthly_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Monthly statistics")
    currency_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Currency statistics")
    spending_patterns: Dict[str, Any] = Field(default_factory=dict, description="Spending pattern analysis")
    anomalies: List[Dict[str, Any]] = Field(default_factory=list, description="Detected anomalies")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        arbitrary_types_allowed = 
        """Pydantic configuration."""
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }

class FileUploadData(BaseModel):
    """
    File upload data structure for processing requests.
    
    Contains file metadata and processing parameters for uploaded
    receipt files before OCR and data extraction.
    """
    
    filename: str = Field(..., min_length=1, description="Original filename")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_type: str = Field(..., description="MIME type of the file")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size limits."""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f"File size exceeds maximum limit of {max_size} bytes")
        return v
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate supported file types."""
        supported_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'image/bmp',
            'text/plain'
        ]
        if v not in supported_types:
            raise ValueError(f"Unsupported file type: {v}")
        return v

# Category mapping for automatic classification
CATEGORY_KEYWORDS = {
    CategoryEnum.GROCERIES: [
        'grocery', 'supermarket', 'market', 'food', 'walmart', 'target', 'kroger',
        'safeway', 'whole foods', 'trader joe', 'costco', 'sam\'s club'
    ],
    CategoryEnum.RESTAURANTS: [
        'restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'mcdonald', 'subway',
        'starbucks', 'dunkin', 'kfc', 'taco bell', 'chipotle', 'dining'
    ],
    CategoryEnum.UTILITIES: [
        'electric', 'gas', 'water', 'internet', 'phone', 'cable', 'utility',
        'verizon', 'at&t', 'comcast', 'spectrum', 'pge', 'edison'
    ],
    CategoryEnum.TRANSPORTATION: [
        'gas station', 'fuel', 'uber', 'lyft', 'taxi', 'bus', 'train', 'airline',
        'parking', 'toll', 'shell', 'chevron', 'exxon', 'bp'
    ],
    CategoryEnum.HEALTHCARE: [
        'pharmacy', 'hospital', 'clinic', 'doctor', 'medical', 'cvs', 'walgreens',
        'rite aid', 'health', 'dental', 'vision'
    ],
    CategoryEnum.ENTERTAINMENT: [
        'movie', 'theater', 'netflix', 'spotify', 'game', 'entertainment',
        'concert', 'show', 'amusement', 'zoo', 'museum'
    ],
    CategoryEnum.SHOPPING: [
        'amazon', 'ebay', 'store', 'mall', 'clothing', 'electronics', 'best buy',
        'home depot', 'lowes', 'macy\'s', 'nordstrom'
    ],
    CategoryEnum.SERVICES: [
        'service', 'repair', 'maintenance', 'cleaning', 'salon', 'barber',
        'dry clean', 'laundry', 'professional'
    ],
    CategoryEnum.EDUCATION: [
        'school', 'university', 'college', 'education', 'tuition', 'books',
        'supplies', 'course', 'training'
    ],
    CategoryEnum.TRAVEL: [
        'hotel', 'motel', 'airbnb', 'flight', 'rental', 'travel', 'vacation',
        'booking', 'expedia', 'trip'
    ]
}

# Currency symbols and patterns for detection
CURRENCY_PATTERNS = {
    CurrencyEnum.USD: [r'\$', r'USD', r'US\$', r'dollar'],
    CurrencyEnum.EUR: [r'€', r'EUR', r'euro'],
    CurrencyEnum.GBP: [r'£', r'GBP', r'pound'],
    CurrencyEnum.CAD: [r'CAD', r'C\$', r'canadian'],
    CurrencyEnum.AUD: [r'AUD', r'A\$', r'australian'],
    CurrencyEnum.JPY: [r'¥', r'JPY', r'yen'],
    CurrencyEnum.CHF: [r'CHF', r'swiss'],
    CurrencyEnum.CNY: [r'CNY', r'yuan', r'rmb']
}

def classify_category(text: str, vendor: str) -> CategoryEnum:
    """
    Automatically classify receipt category based on text content and vendor name.
    
    Args:
        text: Extracted text from receipt
        vendor: Vendor/merchant name
        
    Returns:
        CategoryEnum: Classified category
    """
    combined_text = f"{text} {vendor}".lower()
    
    # Score each category based on keyword matches
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in combined_text)
        if score > 0:
            category_scores[category] = score
    
    # Return category with highest score, or OTHER if no matches
    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    return CategoryEnum.OTHER

def detect_currency(text: str) -> CurrencyEnum:
    """
    Detect currency from receipt text using pattern matching.
    
    Args:
        text: Extracted text from receipt
        
    Returns:
        CurrencyEnum: Detected currency (defaults to USD)
    """
    text_lower = text.lower()
    
    # Check each currency pattern
    for currency, patterns in CURRENCY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return currency
    
    # Default to USD if no currency detected
    return CurrencyEnum.USD
