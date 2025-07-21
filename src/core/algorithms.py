"""
Algorithms Module - Search, Sort, and Analytics Implementation

This module implements core algorithms for searching, sorting, and analyzing receipt data.
Includes optimized search mechanisms, efficient sorting algorithms, and comprehensive
statistical analysis functions.

Time Complexity Analysis:
- Search: O(n) for linear search, O(log n) for indexed search
- Sort: O(n log n) using Python's Timsort algorithm
- Aggregation: O(n) for most statistical computations

Author: Receipt Processing Team
Version: 1.0.0
"""

import re
import statistics
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import Levenshtein

from .models import Receipt, CategoryEnum, CurrencyEnum

@dataclass
class SearchFilters:
    """Data class for search filter parameters."""
    vendor_query: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    category: Optional[CategoryEnum] = None
    currency: Optional[CurrencyEnum] = None
    fuzzy_search: bool = False
    confidence_threshold: float = 0.0

@dataclass
class AnalyticsData:
    """Data class for analytics results."""
    total_receipts: int
    total_amount: Decimal
    average_amount: Decimal
    median_amount: Decimal
    vendor_stats: Dict[str, Dict[str, Any]]
    category_stats: Dict[str, Dict[str, Any]]
    monthly_stats: Dict[str, Dict[str, Any]]
    currency_stats: Dict[str, Dict[str, Any]]
    spending_patterns: Dict[str, Any]
    anomalies: List[Dict[str, Any]]

class ReceiptAnalyzer:
    """
    Advanced analytics engine for receipt data analysis.
    
    Implements efficient algorithms for searching, sorting, and statistical analysis
    of receipt data with optimized time complexity and comprehensive insights.
    """
    
    def __init__(self):
        """Initialize the analyzer with default parameters."""
        self.fuzzy_threshold = 0.8  # Similarity threshold for fuzzy matching
        self.anomaly_threshold = 2.0  # Standard deviations for anomaly detection
    
    def search_receipts(self, receipts: List[Receipt], filters: SearchFilters) -> List[Receipt]:
        """
        Search receipts using multiple criteria with optimized algorithms.
        
        Time Complexity: O(n) where n is the number of receipts
        Space Complexity: O(k) where k is the number of matching receipts
        
        Args:
            receipts: List of receipt objects to search
            filters: Search criteria and parameters
            
        Returns:
            List of receipts matching the search criteria
        """
        filtered_receipts = receipts.copy()
        
        # Vendor search with fuzzy matching support
        if filters.vendor_query:
            if filters.fuzzy_search:
                filtered_receipts = self._fuzzy_vendor_search(
                    filtered_receipts, filters.vendor_query
                )
            else:
                query_lower = filters.vendor_query.lower()
                filtered_receipts = [
                    r for r in filtered_receipts 
                    if query_lower in r.vendor.lower()
                ]
        
        # Date range filtering
        if filters.date_from:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.transaction_date >= filters.date_from
            ]
        
        if filters.date_to:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.transaction_date <= filters.date_to
            ]
        
        # Amount range filtering
        if filters.amount_min is not None:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.amount >= filters.amount_min
            ]
        
        if filters.amount_max is not None:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.amount <= filters.amount_max
            ]
        
        # Category filtering
        if filters.category:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.category == filters.category
            ]
        
        # Currency filtering
        if filters.currency:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.currency == filters.currency
            ]
        
        # Confidence threshold filtering
        if filters.confidence_threshold > 0:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.confidence_score >= filters.confidence_threshold
            ]
        
        return filtered_receipts
    
    def _fuzzy_vendor_search(self, receipts: List[Receipt], query: str) -> List[Receipt]:
        """
        Perform fuzzy string matching for vendor names using Levenshtein distance.
        
        Time Complexity: O(n * m) where n is receipts count, m is average vendor name length
        
        Args:
            receipts: List of receipts to search
            query: Search query string
            
        Returns:
            List of receipts with similar vendor names
        """
        matching_receipts = []
        query_lower = query.lower()
        
        for receipt in receipts:
            vendor_lower = receipt.vendor.lower()
            
            # Calculate similarity ratio
            similarity = Levenshtein.ratio(query_lower, vendor_lower)
            
            if similarity >= self.fuzzy_threshold:
                matching_receipts.append(receipt)
        
        return matching_receipts
    
    def sort_receipts(self, receipts: List[Receipt], sort_by: str, ascending: bool = True) -> List[Receipt]:
        """
        Sort receipts using optimized algorithms with comprehensive field support.
        
        Time Complexity: O(n log n) using Python's Timsort algorithm
        Space Complexity: O(n) for the sorted list
        
        Args:
            receipts: List of receipts to sort
            sort_by: Field to sort by ('date', 'amount', 'vendor', 'category', 'confidence')
            ascending: Sort direction (True for ascending, False for descending)
            
        Returns:
            Sorted list of receipts
        """
        sort_keys = {
            'date': lambda r: r.transaction_date,
            'amount': lambda r: r.amount,
            'vendor': lambda r: r.vendor.lower(),
            'category': lambda r: r.category.value,
            'confidence': lambda r: r.confidence_score,
            'currency': lambda r: r.currency.value
        }
        
        if sort_by not in sort_keys:
            raise ValueError(f"Invalid sort field: {sort_by}")
        
        return sorted(receipts, key=sort_keys[sort_by], reverse=not ascending)
    
    def generate_analytics(self, receipts: List[Receipt]) -> AnalyticsData:
        """
        Generate comprehensive analytics from receipt data.
        
        Time Complexity: O(n) for most computations
        Space Complexity: O(n) for storing aggregated data
        
        Args:
            receipts: List of receipts to analyze
            
        Returns:
            AnalyticsData object with comprehensive insights
        """
        if not receipts:
            return self._empty_analytics()
        
        # Basic statistics
        amounts = [float(r.amount) for r in receipts]
        total_amount = Decimal(str(sum(amounts)))
        average_amount = Decimal(str(statistics.mean(amounts)))
        median_amount = Decimal(str(statistics.median(amounts)))
        
        # Vendor analysis
        vendor_stats = self._analyze_vendors(receipts)
        
        # Category analysis
        category_stats = self._analyze_categories(receipts)
        
        # Monthly trends
        monthly_stats = self._analyze_monthly_trends(receipts)
        
        # Currency analysis
        currency_stats = self._analyze_currencies(receipts)
        
        # Spending patterns
        spending_patterns = self._analyze_spending_patterns(receipts)
        
        # Anomaly detection
        anomalies = self._detect_anomalies(receipts, amounts)
        
        return AnalyticsData(
            total_receipts=len(receipts),
            total_amount=total_amount,
            average_amount=average_amount,
            median_amount=median_amount,
            vendor_stats=vendor_stats,
            category_stats=category_stats,
            monthly_stats=monthly_stats,
            currency_stats=currency_stats,
            spending_patterns=spending_patterns,
            anomalies=anomalies
        )
    
    def _analyze_vendors(self, receipts: List[Receipt]) -> Dict[str, Dict[str, Any]]:
        """Analyze vendor-specific statistics and patterns."""
        vendor_stats = defaultdict(lambda: {
            'count': 0,
            'total_amount': Decimal('0.00'),
            'average_amount': Decimal('0.00'),
            'last_visit': None,
            'frequency_score': 0.0
        })
        
        for receipt in receipts:
            stats = vendor_stats[receipt.vendor]
            stats['count'] += 1
            stats['total_amount'] += receipt.amount
            
            if stats['last_visit'] is None or receipt.transaction_date > stats['last_visit']:
                stats['last_visit'] = receipt.transaction_date
        
        # Calculate derived metrics
        total_receipts = len(receipts)
        for vendor, stats in vendor_stats.items():
            if stats['count'] > 0:
                stats['average_amount'] = stats['total_amount'] / stats['count']
                stats['frequency_score'] = stats['count'] / total_receipts
        
        return dict(vendor_stats)
    
    def _analyze_categories(self, receipts: List[Receipt]) -> Dict[str, Dict[str, Any]]:
        """Analyze category-specific spending patterns."""
        category_stats = defaultdict(lambda: {
            'count': 0,
            'total_amount': Decimal('0.00'),
            'average_amount': Decimal('0.00'),
            'percentage': 0.0
        })
        
        total_amount = sum(r.amount for r in receipts)
        
        for receipt in receipts:
            category = receipt.category.value
            stats = category_stats[category]
            stats['count'] += 1
            stats['total_amount'] += receipt.amount
        
        # Calculate derived metrics
        for category, stats in category_stats.items():
            if stats['count'] > 0:
                stats['average_amount'] = stats['total_amount'] / stats['count']
                stats['percentage'] = float(stats['total_amount'] / total_amount * 100)
        
        return dict(category_stats)
    
    def _analyze_monthly_trends(self, receipts: List[Receipt]) -> Dict[str, Dict[str, Any]]:
        """Analyze monthly spending trends and patterns."""
        monthly_stats = defaultdict(lambda: {
            'count': 0,
            'total_amount': Decimal('0.00'),
            'average_amount': Decimal('0.00')
        })
        
        for receipt in receipts:
            month_key = receipt.transaction_date.strftime('%Y-%m')
            stats = monthly_stats[month_key]
            stats['count'] += 1
            stats['total_amount'] += receipt.amount
        
        # Calculate derived metrics
        for month, stats in monthly_stats.items():
            if stats['count'] > 0:
                stats['average_amount'] = stats['total_amount'] / stats['count']
        
        return dict(monthly_stats)
    
    def _analyze_currencies(self, receipts: List[Receipt]) -> Dict[str, Dict[str, Any]]:
        """Analyze currency distribution and conversion patterns."""
        currency_stats = defaultdict(lambda: {
            'count': 0,
            'total_amount': Decimal('0.00'),
            'percentage': 0.0
        })
        
        total_receipts = len(receipts)
        
        for receipt in receipts:
            currency = receipt.currency.value
            stats = currency_stats[currency]
            stats['count'] += 1
            stats['total_amount'] += receipt.amount
        
        # Calculate percentages
        for currency, stats in currency_stats.items():
            stats['percentage'] = (stats['count'] / total_receipts) * 100
        
        return dict(currency_stats)
    
    def _analyze_spending_patterns(self, receipts: List[Receipt]) -> Dict[str, Any]:
        """Analyze advanced spending patterns and behaviors."""
        if not receipts:
            return {}
        
        # Day of week analysis
        day_patterns = defaultdict(lambda: {'count': 0, 'total_amount': Decimal('0.00')})
        for receipt in receipts:
            day_name = receipt.transaction_date.strftime('%A')
            day_patterns[day_name]['count'] += 1
            day_patterns[day_name]['total_amount'] += receipt.amount
        
        # Time-based patterns
        amounts = [float(r.amount) for r in receipts]
        std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        # Vendor loyalty analysis
        vendor_counts = Counter(r.vendor for r in receipts)
        loyalty_score = len([v for v, c in vendor_counts.items() if c > 1]) / len(vendor_counts)
        
        return {
            'day_patterns': dict(day_patterns),
            'amount_std_dev': std_dev,
            'vendor_loyalty_score': loyalty_score,
            'unique_vendors': len(vendor_counts),
            'repeat_vendors': len([v for v, c in vendor_counts.items() if c > 1])
        }
    
    def _detect_anomalies(self, receipts: List[Receipt], amounts: List[float]) -> List[Dict[str, Any]]:
        """Detect spending anomalies using statistical analysis."""
        if len(amounts) < 3:
            return []
        
        mean_amount = statistics.mean(amounts)
        std_dev = statistics.stdev(amounts)
        threshold = mean_amount + (self.anomaly_threshold * std_dev)
        
        anomalies = []
        for receipt in receipts:
            amount = float(receipt.amount)
            if amount > threshold:
                anomalies.append({
                    'receipt_id': receipt.id,
                    'vendor': receipt.vendor,
                    'amount': receipt.amount,
                    'date': receipt.transaction_date,
                    'deviation': (amount - mean_amount) / std_dev,
                    'type': 'high_amount'
                })
        
        # Detect duplicate receipts (potential duplicates)
        receipt_signatures = {}
        for receipt in receipts:
            signature = f"{receipt.vendor}_{receipt.amount}_{receipt.transaction_date.date()}"
            if signature in receipt_signatures:
                anomalies.append({
                    'receipt_id': receipt.id,
                    'vendor': receipt.vendor,
                    'amount': receipt.amount,
                    'date': receipt.transaction_date,
                    'type': 'potential_duplicate',
                    'similar_to': receipt_signatures[signature]
                })
            else:
                receipt_signatures[signature] = receipt.id
        
        return anomalies
    
    def _empty_analytics(self) -> AnalyticsData:
        """Return empty analytics data structure."""
        return AnalyticsData(
            total_receipts=0,
            total_amount=Decimal('0.00'),
            average_amount=Decimal('0.00'),
            median_amount=Decimal('0.00'),
            vendor_stats={},
            category_stats={},
            monthly_stats={},
            currency_stats={},
            spending_patterns={},
            anomalies=[]
        )
    
    def get_top_vendors(self, receipts: List[Receipt], limit: int = 10) -> List[Tuple[str, Decimal, int]]:
        """
        Get top vendors by total spending.
        
        Args:
            receipts: List of receipts
            limit: Maximum number of vendors to return
            
        Returns:
            List of tuples (vendor_name, total_amount, transaction_count)
        """
        vendor_totals = defaultdict(lambda: {'amount': Decimal('0.00'), 'count': 0})
        
        for receipt in receipts:
            vendor_totals[receipt.vendor]['amount'] += receipt.amount
            vendor_totals[receipt.vendor]['count'] += 1
        
        # Sort by total amount and return top vendors
        sorted_vendors = sorted(
            vendor_totals.items(),
            key=lambda x: x[1]['amount'],
            reverse=True
        )
        
        return [
            (vendor, data['amount'], data['count'])
            for vendor, data in sorted_vendors[:limit]
        ]
    
    def calculate_spending_velocity(self, receipts: List[Receipt], days: int = 30) -> Dict[str, float]:
        """
        Calculate spending velocity (rate of spending over time).
        
        Args:
            receipts: List of receipts
            days: Number of days to analyze
            
        Returns:
            Dictionary with velocity metrics
        """
        if not receipts:
            return {'daily_average': 0.0, 'weekly_average': 0.0, 'monthly_average': 0.0}
        
        # Filter receipts to specified time period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_receipts = [r for r in receipts if r.transaction_date >= cutoff_date]
        
        if not recent_receipts:
            return {'daily_average': 0.0, 'weekly_average': 0.0, 'monthly_average': 0.0}
        
        total_amount = sum(float(r.amount) for r in recent_receipts)
        actual_days = (datetime.now() - min(r.transaction_date for r in recent_receipts)).days + 1
        
        daily_avg = total_amount / actual_days
        weekly_avg = daily_avg * 7
        monthly_avg = daily_avg * 30
        
        return {
            'daily_average': daily_avg,
            'weekly_average': weekly_avg,
            'monthly_average': monthly_avg,
            'total_amount': total_amount,
            'period_days': actual_days
        }
