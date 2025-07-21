"""
Search, sorting, and analytics algorithms for receipt processing.
Implements efficient data processing with time complexity analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
from collections import defaultdict, Counter
import statistics
import re

from .models import Receipt, SearchFilters, AnalyticsData


class ReceiptAnalyzer:
    """
    Advanced analytics and search algorithms for receipt data.
    
    Provides efficient search, sorting, and statistical analysis
    with optimized algorithms and comprehensive metrics.
    """
    
    def __init__(self):
        """Initialize analyzer with logging."""
        self.logger = logging.getLogger(__name__)
    
    def search_receipts(self, receipts: List[Receipt], filters: SearchFilters) -> List[Receipt]:
        """
        Advanced search with multiple criteria.
        
        Time Complexity: O(n) where n is the number of receipts
        Space Complexity: O(k) where k is the number of matching receipts
        
        Args:
            receipts: List of receipts to search
            filters: Search criteria
            
        Returns:
            Filtered list of receipts
        """
        if not receipts:
            return []
        
        filtered_receipts = receipts.copy()
        
        # Apply vendor search (case-insensitive substring matching)
        if filters.vendor_query:
            query_lower = filters.vendor_query.lower()
            filtered_receipts = [
                r for r in filtered_receipts 
                if query_lower in r.vendor.lower()
            ]
        
        # Apply date range filters
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
        
        # Apply amount range filters
        if filters.amount_min:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.amount >= filters.amount_min
            ]
        
        if filters.amount_max:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.amount <= filters.amount_max
            ]
        
        # Apply category filter
        if filters.category:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.category == filters.category
            ]
        
        # Apply currency filter
        if filters.currency:
            filtered_receipts = [
                r for r in filtered_receipts 
                if r.currency == filters.currency
            ]
        
        self.logger.info(f"Search filtered {len(receipts)} receipts to {len(filtered_receipts)}")
        return filtered_receipts
    
    def fuzzy_search_vendors(self, receipts: List[Receipt], query: str, threshold: float = 0.6) -> List[Receipt]:
        """
        Fuzzy search for vendor names using Levenshtein distance.
        
        Time Complexity: O(n * m) where n is receipts count, m is average vendor name length
        
        Args:
            receipts: List of receipts to search
            query: Search query
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            Receipts with similar vendor names
        """
        if not query.strip():
            return receipts
        
        query_lower = query.lower().strip()
        matches = []
        
        for receipt in receipts:
            vendor_lower = receipt.vendor.lower()
            similarity = self._calculate_similarity(query_lower, vendor_lower)
            
            if similarity >= threshold:
                matches.append((receipt, similarity))
        
        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches]
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity using Levenshtein distance.
        
        Args:
            s1, s2: Strings to compare
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not s1 or not s2:
            return 0.0
        
        # Simple implementation of Levenshtein distance
        len1, len2 = len(s1), len(s2)
        
        # Create matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        # Calculate similarity
        max_len = max(len1, len2)
        if max_len == 0:
            return 1.0
        
        distance = matrix[len1][len2]
        similarity = 1.0 - (distance / max_len)
        return max(0.0, similarity)
    
    def sort_receipts(self, receipts: List[Receipt], sort_by: str, ascending: bool = True) -> List[Receipt]:
        """
        Sort receipts using optimized algorithms.
        
        Time Complexity: O(n log n) using Python's Timsort
        Space Complexity: O(n) for the sorted list
        
        Args:
            receipts: List of receipts to sort
            sort_by: Field to sort by ('date', 'amount', 'vendor', 'category')
            ascending: Sort direction
            
        Returns:
            Sorted list of receipts
        """
        if not receipts:
            return []
        
        # Define sort key functions
        sort_keys = {
            'date': lambda r: r.transaction_date,
            'amount': lambda r: r.amount,
            'vendor': lambda r: r.vendor.lower(),
            'category': lambda r: r.category,
            'created': lambda r: r.created_at or datetime.min,
        }
        
        if sort_by not in sort_keys:
            self.logger.warning(f"Invalid sort field: {sort_by}. Using 'date'.")
            sort_by = 'date'
        
        try:
            sorted_receipts = sorted(receipts, key=sort_keys[sort_by], reverse=not ascending)
            self.logger.info(f"Sorted {len(receipts)} receipts by {sort_by} ({'asc' if ascending else 'desc'})")
            return sorted_receipts
        except Exception as e:
            self.logger.error(f"Sorting failed: {e}")
            return receipts
    
    def generate_analytics(self, receipts: List[Receipt]) -> AnalyticsData:
        """
        Generate comprehensive analytics from receipt data.
        
        Time Complexity: O(n) for most operations, O(n log n) for sorting
        
        Args:
            receipts: List of receipts to analyze
            
        Returns:
            AnalyticsData with comprehensive statistics
        """
        if not receipts:
            return AnalyticsData()
        
        # Basic statistics
        total_receipts = len(receipts)
        amounts = [float(r.amount) for r in receipts]
        total_amount = Decimal(str(sum(amounts)))
        average_amount = Decimal(str(statistics.mean(amounts)))
        
        # Date range
        dates = [r.transaction_date for r in receipts]
        date_range = (min(dates), max(dates))
        
        # Top vendors analysis
        vendor_stats = defaultdict(lambda: {'count': 0, 'total_amount': Decimal('0.00')})
        for receipt in receipts:
            vendor_stats[receipt.vendor]['count'] += 1
            vendor_stats[receipt.vendor]['total_amount'] += receipt.amount
        
        top_vendors = sorted(
            [
                {
                    'vendor': vendor,
                    'count': stats['count'],
                    'total_amount': float(stats['total_amount'])
                }
                for vendor, stats in vendor_stats.items()
            ],
            key=lambda x: x['total_amount'],
            reverse=True
        )[:10]
        
        # Category breakdown
        category_stats = defaultdict(lambda: {'count': 0, 'total_amount': Decimal('0.00')})
        for receipt in receipts:
            category_stats[receipt.category]['count'] += 1
            category_stats[receipt.category]['total_amount'] += receipt.amount
        
        category_breakdown = [
            {
                'category': category,
                'count': stats['count'],
                'total_amount': float(stats['total_amount'])
            }
            for category, stats in category_stats.items()
        ]
        
        # Monthly trends
        monthly_stats = defaultdict(lambda: {'count': 0, 'total_amount': Decimal('0.00')})
        for receipt in receipts:
            month_key = receipt.transaction_date.strftime('%Y-%m')
            monthly_stats[month_key]['count'] += 1
            monthly_stats[month_key]['total_amount'] += receipt.amount
        
        monthly_trends = sorted(
            [
                {
                    'month': month,
                    'count': stats['count'],
                    'total_amount': float(stats['total_amount'])
                }
                for month, stats in monthly_stats.items()
            ],
            key=lambda x: x['month'],
            reverse=True
        )[:12]
        
        return AnalyticsData(
            total_receipts=total_receipts,
            total_amount=total_amount,
            average_amount=average_amount,
            date_range=date_range,
            top_vendors=top_vendors,
            category_breakdown=category_breakdown,
            monthly_trends=monthly_trends
        )
    
    def detect_spending_patterns(self, receipts: List[Receipt]) -> Dict[str, Any]:
        """
        Detect spending patterns and anomalies.
        
        Args:
            receipts: List of receipts to analyze
            
        Returns:
            Dictionary with pattern analysis
        """
        if not receipts:
            return {}
        
        patterns = {}
        
        # Day of week analysis
        day_spending = defaultdict(list)
        for receipt in receipts:
            day_name = receipt.transaction_date.strftime('%A')
            day_spending[day_name].append(float(receipt.amount))
        
        patterns['day_of_week'] = {
            day: {
                'count': len(amounts),
                'total': sum(amounts),
                'average': statistics.mean(amounts) if amounts else 0
            }
            for day, amounts in day_spending.items()
        }
        
        # Monthly spending trends
        monthly_spending = defaultdict(list)
        for receipt in receipts:
            month = receipt.transaction_date.strftime('%Y-%m')
            monthly_spending[month].append(float(receipt.amount))
        
        patterns['monthly_trends'] = {
            month: {
                'count': len(amounts),
                'total': sum(amounts),
                'average': statistics.mean(amounts) if amounts else 0
            }
            for month, amounts in monthly_spending.items()
        }
        
        # Spending anomalies (amounts > 2 standard deviations from mean)
        amounts = [float(r.amount) for r in receipts]
        if len(amounts) > 1:
            mean_amount = statistics.mean(amounts)
            std_dev = statistics.stdev(amounts)
            threshold = mean_amount + (2 * std_dev)
            
            anomalies = [
                {
                    'receipt_id': r.id,
                    'vendor': r.vendor,
                    'amount': float(r.amount),
                    'date': r.transaction_date.isoformat(),
                    'deviation': float(r.amount) - mean_amount
                }
                for r in receipts
                if float(r.amount) > threshold
            ]
            
            patterns['anomalies'] = anomalies
        
        # Vendor frequency analysis
        vendor_frequency = Counter(r.vendor for r in receipts)
        patterns['frequent_vendors'] = [
            {'vendor': vendor, 'count': count}
            for vendor, count in vendor_frequency.most_common(10)
        ]
        
        return patterns
    
    def calculate_category_trends(self, receipts: List[Receipt], days: int = 30) -> Dict[str, Any]:
        """
        Calculate spending trends by category over time.
        
        Args:
            receipts: List of receipts
            days: Number of days to analyze
            
        Returns:
            Category trend analysis
        """
        cutoff_date = date.today() - timedelta(days=days)
        recent_receipts = [r for r in receipts if r.transaction_date >= cutoff_date]
        
        if not recent_receipts:
            return {}
        
        # Group by category and date
        category_daily = defaultdict(lambda: defaultdict(Decimal))
        
        for receipt in recent_receipts:
            date_key = receipt.transaction_date.isoformat()
            category_daily[receipt.category][date_key] += receipt.amount
        
        trends = {}
        for category, daily_amounts in category_daily.items():
            amounts = list(daily_amounts.values())
            trends[category] = {
                'total_amount': float(sum(amounts)),
                'average_daily': float(sum(amounts) / days),
                'transaction_count': len(amounts),
                'daily_data': {
                    date_str: float(amount) 
                    for date_str, amount in daily_amounts.items()
                }
            }
        
        return trends
    
    def find_duplicate_receipts(self, receipts: List[Receipt], threshold: float = 0.9) -> List[List[Receipt]]:
        """
        Find potential duplicate receipts based on similarity.
        
        Args:
            receipts: List of receipts to check
            threshold: Similarity threshold for duplicates
            
        Returns:
            List of groups of potential duplicates
        """
        if len(receipts) < 2:
            return []
        
        duplicates = []
        processed = set()
        
        for i, receipt1 in enumerate(receipts):
            if i in processed:
                continue
            
            group = [receipt1]
            processed.add(i)
            
            for j, receipt2 in enumerate(receipts[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_receipt_similarity(receipt1, receipt2)
                if similarity >= threshold:
                    group.append(receipt2)
                    processed.add(j)
            
            if len(group) > 1:
                duplicates.append(group)
        
        return duplicates
    
    def _calculate_receipt_similarity(self, r1: Receipt, r2: Receipt) -> float:
        """
        Calculate similarity between two receipts.
        
        Args:
            r1, r2: Receipts to compare
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Weight factors for different fields
        weights = {
            'vendor': 0.4,
            'amount': 0.3,
            'date': 0.2,
            'category': 0.1
        }
        
        similarity_score = 0.0
        
        # Vendor similarity
        vendor_sim = self._calculate_similarity(r1.vendor.lower(), r2.vendor.lower())
        similarity_score += weights['vendor'] * vendor_sim
        
        # Amount similarity (exact match or very close)
        amount_diff = abs(r1.amount - r2.amount)
        if amount_diff == 0:
            amount_sim = 1.0
        elif amount_diff <= Decimal('0.01'):  # Within 1 cent
            amount_sim = 0.9
        elif amount_diff <= Decimal('1.00'):  # Within $1
            amount_sim = 0.5
        else:
            amount_sim = max(0.0, 1.0 - float(amount_diff) / float(max(r1.amount, r2.amount)))
        
        similarity_score += weights['amount'] * amount_sim
        
        # Date similarity (same day = 1.0, within week = 0.5, etc.)
        date_diff = abs((r1.transaction_date - r2.transaction_date).days)
        if date_diff == 0:
            date_sim = 1.0
        elif date_diff <= 1:
            date_sim = 0.8
        elif date_diff <= 7:
            date_sim = 0.5
        else:
            date_sim = max(0.0, 1.0 - date_diff / 30.0)
        
        similarity_score += weights['date'] * date_sim
        
        # Category similarity
        category_sim = 1.0 if r1.category == r2.category else 0.0
        similarity_score += weights['category'] * category_sim
        
        return similarity_score
