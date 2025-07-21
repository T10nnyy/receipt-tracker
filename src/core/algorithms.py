import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from difflib import SequenceMatcher
import Levenshtein

from .models import Receipt, ReceiptItem

logger = logging.getLogger(__name__)

class ReceiptAnalyzer:
    """Analyzes receipts for patterns, insights, and search functionality"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'store', 'shop', 'market', 'receipt', 'total', 'subtotal', 'tax', 'amount'
        }
    
    def search_receipts(self, query: str, receipts: List[Receipt]) -> List[Receipt]:
        """Search receipts using fuzzy matching and relevance scoring"""
        if not query.strip():
            return receipts
        
        query_lower = query.lower().strip()
        scored_receipts = []
        
        for receipt in receipts:
            score = self._calculate_relevance_score(query_lower, receipt)
            if score > 0:
                scored_receipts.append((receipt, score))
        
        # Sort by relevance score (descending)
        scored_receipts.sort(key=lambda x: x[1], reverse=True)
        
        return [receipt for receipt, score in scored_receipts]
    
    def _calculate_relevance_score(self, query: str, receipt: Receipt) -> float:
        """Calculate relevance score for a receipt based on query"""
        score = 0.0
        
        # Search in merchant name (high weight)
        if receipt.merchant_name:
            merchant_similarity = self._fuzzy_match(query, receipt.merchant_name.lower())
            score += merchant_similarity * 3.0
        
        # Search in raw text (medium weight)
        if receipt.raw_text:
            text_similarity = self._text_contains_query(query, receipt.raw_text.lower())
            score += text_similarity * 1.5
        
        # Search in items (high weight)
        for item in receipt.items:
            item_similarity = self._fuzzy_match(query, item.name.lower())
            score += item_similarity * 2.0
        
        # Search in notes (medium weight)
        if receipt.notes:
            notes_similarity = self._fuzzy_match(query, receipt.notes.lower())
            score += notes_similarity * 1.0
        
        # Exact matches get bonus points
        if query in receipt.raw_text.lower():
            score += 2.0
        
        return score
    
    def _fuzzy_match(self, query: str, text: str) -> float:
        """Calculate fuzzy match score between query and text"""
        if not query or not text:
            return 0.0
        
        # Direct substring match
        if query in text:
            return 1.0
        
        # Levenshtein distance based similarity
        max_len = max(len(query), len(text))
        if max_len == 0:
            return 0.0
        
        distance = Levenshtein.distance(query, text)
        similarity = 1.0 - (distance / max_len)
        
        # Only return meaningful similarities
        return similarity if similarity > 0.6 else 0.0
    
    def _text_contains_query(self, query: str, text: str) -> float:
        """Check if text contains query words with partial matching"""
        query_words = set(query.split()) - self.stop_words
        text_words = set(text.split())
        
        if not query_words:
            return 0.0
        
        matches = 0
        for query_word in query_words:
            # Exact word match
            if query_word in text_words:
                matches += 1
                continue
            
            # Partial word match
            for text_word in text_words:
                if len(query_word) > 3 and query_word in text_word:
                    matches += 0.5
                    break
        
        return matches / len(query_words)
    
    def generate_analytics(self, receipts: List[Receipt]) -> Dict[str, Any]:
        """Generate comprehensive analytics from receipts"""
        if not receipts:
            return self._empty_analytics()
        
        analytics = {
            'total_receipts': len(receipts),
            'total_amount': 0.0,
            'average_amount': 0.0,
            'unique_merchants': 0,
            'date_range': {},
            'top_merchants': {},
            'spending_by_date': {},
            'monthly_breakdown': [],
            'category_breakdown': {},
            'receipts_this_month': 0,
            'amount_this_month': 0.0
        }
        
        try:
            # Basic calculations
            valid_amounts = [r.total_amount for r in receipts if r.total_amount and r.total_amount > 0]
            analytics['total_amount'] = sum(valid_amounts)
            analytics['average_amount'] = np.mean(valid_amounts) if valid_amounts else 0.0
            
            # Merchant analysis
            merchant_spending = defaultdict(float)
            merchants = set()
            
            for receipt in receipts:
                if receipt.merchant_name:
                    merchants.add(receipt.merchant_name)
                    if receipt.total_amount:
                        merchant_spending[receipt.merchant_name] += receipt.total_amount
            
            analytics['unique_merchants'] = len(merchants)
            analytics['top_merchants'] = dict(
                sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            
            # Date analysis
            dates_with_amounts = [
                (r.receipt_date, r.total_amount) 
                for r in receipts 
                if r.receipt_date and r.total_amount
            ]
            
            if dates_with_amounts:
                dates, amounts = zip(*dates_with_amounts)
                analytics['date_range'] = {
                    'start': min(dates).isoformat(),
                    'end': max(dates).isoformat()
                }
                
                # Spending by date
                daily_spending = defaultdict(float)
                for date, amount in dates_with_amounts:
                    date_str = date.strftime('%Y-%m-%d')
                    daily_spending[date_str] += amount
                
                analytics['spending_by_date'] = dict(daily_spending)
                
                # Monthly breakdown
                monthly_data = defaultdict(lambda: {'count': 0, 'total': 0.0})
                current_month = datetime.now().replace(day=1)
                
                for date, amount in dates_with_amounts:
                    month_key = date.strftime('%Y-%m')
                    monthly_data[month_key]['count'] += 1
                    monthly_data[month_key]['total'] += amount
                    
                    # This month's data
                    if date >= current_month:
                        analytics['receipts_this_month'] += 1
                        analytics['amount_this_month'] += amount
                
                analytics['monthly_breakdown'] = [
                    {
                        'month': month,
                        'count': data['count'],
                        'total': data['total'],
                        'average': data['total'] / data['count']
                    }
                    for month, data in sorted(monthly_data.items(), reverse=True)
                ]
            
            # Category analysis
            category_spending = defaultdict(float)
            for receipt in receipts:
                if receipt.category and receipt.total_amount:
                    category_spending[receipt.category] += receipt.total_amount
            
             
                    category_spending[receipt.category] += receipt.total_amount
            
            analytics['category_breakdown'] = dict(category_spending)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return self._empty_analytics()
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'total_receipts': 0,
            'total_amount': 0.0,
            'average_amount': 0.0,
            'unique_merchants': 0,
            'date_range': {},
            'top_merchants': {},
            'spending_by_date': {},
            'monthly_breakdown': [],
            'category_breakdown': {},
            'receipts_this_month': 0,
            'amount_this_month': 0.0
        }
    
    def detect_patterns(self, receipts: List[Receipt]) -> List[Dict[str, Any]]:
        """Detect spending patterns and generate insights"""
        patterns = []
        
        if len(receipts) < 2:
            return patterns
        
        try:
            # Frequent merchants pattern
            merchant_counts = Counter(
                r.merchant_name for r in receipts 
                if r.merchant_name
            )
            
            if merchant_counts:
                most_frequent = merchant_counts.most_common(1)[0]
                if most_frequent[1] >= 3:
                    patterns.append({
                        'type': 'frequent_merchant',
                        'description': f"You frequently shop at {most_frequent[0]} ({most_frequent[1]} times)",
                        'confidence': min(most_frequent[1] / len(receipts), 1.0)
                    })
            
            # High spending pattern
            amounts = [r.total_amount for r in receipts if r.total_amount]
            if amounts:
                avg_amount = np.mean(amounts)
                high_spending = [a for a in amounts if a > avg_amount * 2]
                
                if len(high_spending) > len(amounts) * 0.1:  # More than 10% are high spending
                    patterns.append({
                        'type': 'high_spending',
                        'description': f"You have {len(high_spending)} receipts with unusually high amounts (>${avg_amount * 2:.2f}+)",
                        'confidence': len(high_spending) / len(amounts)
                    })
            
            # Weekend vs weekday spending
            weekend_amounts = []
            weekday_amounts = []
            
            for receipt in receipts:
                if receipt.receipt_date and receipt.total_amount:
                    if receipt.receipt_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                        weekend_amounts.append(receipt.total_amount)
                    else:
                        weekday_amounts.append(receipt.total_amount)
            
            if weekend_amounts and weekday_amounts:
                weekend_avg = np.mean(weekend_amounts)
                weekday_avg = np.mean(weekday_amounts)
                
                if weekend_avg > weekday_avg * 1.5:
                    patterns.append({
                        'type': 'weekend_spending',
                        'description': f"You spend significantly more on weekends (${weekend_avg:.2f} vs ${weekday_avg:.2f})",
                        'confidence': min((weekend_avg - weekday_avg) / weekday_avg, 1.0)
                    })
            
            # Monthly spending trend
            monthly_totals = defaultdict(float)
            for receipt in receipts:
                if receipt.receipt_date and receipt.total_amount:
                    month_key = receipt.receipt_date.strftime('%Y-%m')
                    monthly_totals[month_key] += receipt.total_amount
            
            if len(monthly_totals) >= 3:
                sorted_months = sorted(monthly_totals.items())
                recent_months = sorted_months[-3:]
                
                if len(recent_months) == 3:
                    trend = []
                    for i in range(1, len(recent_months)):
                        current = recent_months[i][1]
                        previous = recent_months[i-1][1]
                        change = (current - previous) / previous if previous > 0 else 0
                        trend.append(change)
                    
                    avg_trend = np.mean(trend)
                    if avg_trend > 0.2:  # 20% increase trend
                        patterns.append({
                            'type': 'increasing_spending',
                            'description': f"Your spending has been increasing over the last 3 months (average {avg_trend*100:.1f}% per month)",
                            'confidence': min(abs(avg_trend), 1.0)
                        })
                    elif avg_trend < -0.2:  # 20% decrease trend
                        patterns.append({
                            'type': 'decreasing_spending',
                            'description': f"Your spending has been decreasing over the last 3 months (average {abs(avg_trend)*100:.1f}% per month)",
                            'confidence': min(abs(avg_trend), 1.0)
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    def categorize_receipt(self, receipt: Receipt) -> str:
        """Automatically categorize a receipt based on merchant and items"""
        try:
            # Category keywords mapping
            categories = {
                'Groceries': ['grocery', 'supermarket', 'market', 'food', 'walmart', 'target', 'kroger', 'safeway'],
                'Restaurants': ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'diner', 'bistro', 'grill'],
                'Gas': ['gas', 'fuel', 'shell', 'exxon', 'bp', 'chevron', 'mobil'],
                'Shopping': ['store', 'shop', 'mall', 'retail', 'amazon', 'ebay'],
                'Healthcare': ['pharmacy', 'medical', 'doctor', 'hospital', 'clinic', 'cvs', 'walgreens'],
                'Entertainment': ['movie', 'theater', 'cinema', 'game', 'entertainment', 'netflix'],
                'Transportation': ['uber', 'lyft', 'taxi', 'bus', 'train', 'parking'],
                'Utilities': ['electric', 'water', 'internet', 'phone', 'utility']
            }
            
            text_to_check = ""
            if receipt.merchant_name:
                text_to_check += receipt.merchant_name.lower() + " "
            if receipt.raw_text:
                text_to_check += receipt.raw_text.lower() + " "
            
            # Score each category
            category_scores = {}
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in text_to_check)
                if score > 0:
                    category_scores[category] = score
            
            # Return the highest scoring category
            if category_scores:
                return max(category_scores, key=category_scores.get)
            
            return 'Other'
            
        except Exception as e:
            logger.error(f"Error categorizing receipt: {e}")
            return 'Other'
