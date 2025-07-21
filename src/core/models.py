"""
Data models for receipt processing application.
Implements Pydantic models with comprehensive validation.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator, root_validator
import re


class CategoryEnum(str, Enum):
    """Predefined receipt categories."""
    FOOD = "Food & Dining"
    GROCERIES = "Groceries"
    TRANSPORTATION = "Transportation"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    UTILITIES = "Utilities"
    HEALTHCARE = "Healthcare"
    BUSINESS = "Business"
    OTHER = "Other"


class CurrencyEnum(str, Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class Receipt(BaseModel):
    """
    Receipt data model with comprehensive validation.
    
    Attributes:
        id: Unique identifier (auto-generated)
        vendor: Merchant/vendor name
        transaction_date: Date of transaction
        amount: Transaction amount (must be positive)
        category: Receipt category
        currency: Currency code
        source_file: Original filename
        extracted_text: Raw extracted text
        confidence_score: OCR confidence (0-100)
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    
    id: Optional[int] = None
    vendor: str = Field(..., min_length=1, max_length=200)
    transaction_date: date = Field(...)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    category: CategoryEnum = Field(default=CategoryEnum.OTHER)
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD)
    source_file: str = Field(..., min_length=1, max_length=255)
    extracted_text: Optional[str] = Field(default="", max_length=10000)
    confidence_score: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('vendor')
    def validate_vendor(cls, v):
        """Clean and validate vendor name."""
        if not v or not v.strip():
            raise ValueError("Vendor name cannot be empty")
        # Remove excessive whitespace and special characters
        cleaned = re.sub(r'\s+', ' ', v.strip())
        cleaned = re.sub(r'[^\w\s\-&.,]', '', cleaned)
        return cleaned[:200]  # Truncate if too long
    
    @validator('amount')
    def validate_amount(cls, v):
        """Ensure amount is positive and reasonable."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > Decimal('999999.99'):
            raise ValueError("Amount exceeds maximum allowed value")
        return v.quantize(Decimal('0.01'))  # Round to 2 decimal places
    
    @validator('transaction_date')
    def validate_date(cls, v):
        """Validate transaction date is not in the future."""
        if v > date.today():
            raise ValueError("Transaction date cannot be in the future")
        return v
    
    @root_validator
    def validate_model(cls, values):
        """Cross-field validation."""
        # Set timestamps if not provided
        now = datetime.now()
        if not values.get('created_at'):
            values['created_at'] = now
        values['updated_at'] = now
        
        return values
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True


class SearchFilters(BaseModel):
    """Search and filter parameters."""
    
    vendor_query: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    category: Optional[CategoryEnum] = None
    currency: Optional[CurrencyEnum] = None
    
    @validator('vendor_query')
    def clean_vendor_query(cls, v):
        """Clean search query."""
        if v:
            return v.strip()[:100]  # Limit length
        return v
    
    @root_validator
    def validate_ranges(cls, values):
        """Validate date and amount ranges."""
        date_from = values.get('date_from')
        date_to = values.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValueError("Start date must be before end date")
        
        amount_min = values.get('amount_min')
        amount_max = values.get('amount_max')
        
        if amount_min and amount_max and amount_min > amount_max:
            raise ValueError("Minimum amount must be less than maximum amount")
        
        return values


class ProcessingResult(BaseModel):
    """Result of file processing operation."""
    
    success: bool
    receipt: Optional[Receipt] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    processing_time: Optional[float] = None
    
    class Config:
        arbitrary_types_allowed = True


class AnalyticsData(BaseModel):
    """Analytics and statistics data."""
    
    total_receipts: int = 0
    total_amount: Decimal = Field(default=Decimal('0.00'))
    average_amount: Decimal = Field(default=Decimal('0.00'))
    date_range: Optional[tuple] = None
    top_vendors: List[dict] = Field(default_factory=list)
    category_breakdown: List[dict] = Field(default_factory=list)
    monthly_trends: List[dict] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
