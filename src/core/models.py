from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

@dataclass
class ReceiptItem:
    """Represents an individual item on a receipt"""
    name: str
    price: float
    quantity: int = 1
    category: Optional[str] = None
    
    def __post_init__(self):
        """Validate data after initialization"""
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")

@dataclass
class Receipt:
    """Represents a complete receipt"""
    filename: str
    raw_text: str
    upload_date: datetime
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    merchant_name: Optional[str] = None
    receipt_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    items: List[ReceiptItem] = field(default_factory=list)
    category: Optional[str] = None
    notes: Optional[str] = None
    confidence_score: Optional[float] = None
    
    def __post_init__(self):
        """Validate data after initialization"""
        if self.total_amount is not None and self.total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        if self.tax_amount is not None and self.tax_amount < 0:
            raise ValueError("Tax amount cannot be negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary for database storage"""
        return {
            'id': self.id,
            'filename': self.filename,
            'raw_text': self.raw_text,
            'upload_date': self.upload_date.isoformat(),
            'merchant_name': self.merchant_name,
            'receipt_date': self.receipt_date.isoformat() if self.receipt_date else None,
            'total_amount': self.total_amount,
            'tax_amount': self.tax_amount,
            'category': self.category,
            'notes': self.notes,
            'confidence_score': self.confidence_score,
            'items': [
                {
                    'name': item.name,
                    'price': item.price,
                    'quantity': item.quantity,
                    'category': item.category
                }
                for item in self.items
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Receipt':
        """Create receipt from dictionary"""
        items = []
        if data.get('items'):
            items = [
                ReceiptItem(
                    name=item['name'],
                    price=item['price'],
                    quantity=item.get('quantity', 1),
                    category=item.get('category')
                )
                for item in data['items']
            ]
        
        return cls(
            id=data.get('id'),
            filename=data['filename'],
            raw_text=data['raw_text'],
            upload_date=datetime.fromisoformat(data['upload_date']),
            merchant_name=data.get('merchant_name'),
            receipt_date=datetime.fromisoformat(data['receipt_date']) if data.get('receipt_date') else None,
            total_amount=data.get('total_amount'),
            tax_amount=data.get('tax_amount'),
            items=items,
            category=data.get('category'),
            notes=data.get('notes'),
            confidence_score=data.get('confidence_score')
        )

class AnalyticsResult(BaseModel):
    """Represents analytics results"""
    total_receipts: int
    total_amount: float
    average_amount: float
    unique_merchants: int
    date_range: Dict[str, str]
    top_merchants: Dict[str, float]
    spending_by_date: Dict[str, float]
    monthly_breakdown: List[Dict[str, Any]]
    category_breakdown: Dict[str, float]

class SearchResult(BaseModel):
    """Represents search results"""
    receipts: List[Receipt]
    total_count: int
    query: str
    filters_applied: Dict[str, Any]
