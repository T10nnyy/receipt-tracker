from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

@dataclass
class ReceiptItem:
    """Represents an item on a receipt"""
    name: str
    price: float
    quantity: int = 1
    category: str = "Other"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
            'category': self.category
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptItem':
        """Create from dictionary"""
        return cls(
            name=data.get('name', ''),
            price=float(data.get('price', 0.0)),
            quantity=int(data.get('quantity', 1)),
            category=data.get('category', 'Other')
        )

@dataclass
class Receipt:
    """Represents a complete receipt"""
    store_name: str
    date: datetime
    total: float
    items: List[ReceiptItem] = field(default_factory=list)
    category: str = "Other"
    tax: float = 0.0
    tip: float = 0.0
    payment_method: str = "Unknown"
    receipt_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'receipt_id': self.receipt_id,
            'store_name': self.store_name,
            'date': self.date.isoformat() if self.date else None,
            'total': self.total,
            'items': [item.to_dict() for item in self.items],
            'category': self.category,
            'tax': self.tax,
            'tip': self.tip,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Receipt':
        """Create from dictionary"""
        items = []
        if 'items' in data and data['items']:
            if isinstance(data['items'], str):
                # Parse JSON string
                try:
                    items_data = json.loads(data['items'])
                    items = [ReceiptItem.from_dict(item) for item in items_data]
                except json.JSONDecodeError:
                    items = []
            elif isinstance(data['items'], list):
                items = [ReceiptItem.from_dict(item) for item in data['items']]
        
        # Parse dates
        date = data.get('date')
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            except ValueError:
                date = datetime.now()
        elif date is None:
            date = datetime.now()
        
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                created_at = datetime.now()
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            receipt_id=data.get('receipt_id'),
            store_name=data.get('store_name', ''),
            date=date,
            total=float(data.get('total', 0.0)),
            items=items,
            category=data.get('category', 'Other'),
            tax=float(data.get('tax', 0.0)),
            tip=float(data.get('tip', 0.0)),
            payment_method=data.get('payment_method', 'Unknown'),
            created_at=created_at
        )
    
    def get_item_count(self) -> int:
        """Get total number of items"""
        return sum(item.quantity for item in self.items)
    
    def get_subtotal(self) -> float:
        """Calculate subtotal (total - tax - tip)"""
        return self.total - self.tax - self.tip
    
    def add_item(self, item: ReceiptItem):
        """Add an item to the receipt"""
        self.items.append(item)
    
    def remove_item(self, index: int):
        """Remove an item by index"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
    
    def get_items_by_category(self) -> Dict[str, List[ReceiptItem]]:
        """Group items by category"""
        categories = {}
        for item in self.items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        return categories

@dataclass
class ReceiptStatistics:
    """Statistics about receipts"""
    total_receipts: int = 0
    total_spent: float = 0.0
    average_receipt: float = 0.0
    most_frequent_store: str = ""
    most_expensive_receipt: float = 0.0
    receipts_this_month: int = 0
    spending_this_month: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_receipts': self.total_receipts,
            'total_spent': self.total_spent,
            'average_receipt': self.average_receipt,
            'most_frequent_store': self.most_frequent_store,
            'most_expensive_receipt': self.most_expensive_receipt,
            'receipts_this_month': self.receipts_this_month,
            'spending_this_month': self.spending_this_month
        }
