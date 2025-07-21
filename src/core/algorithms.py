import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class ReceiptAnalyzer:
    """Advanced analytics for receipt data"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.scaler = StandardScaler()
    
    def analyze_spending_patterns(self, receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze spending patterns from receipt data"""
        if not receipts:
            return {}
        
        df = pd.DataFrame(receipts)
        
        # Convert date strings to datetime
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.day_name()
        df['month'] = df['date'].dt.month_name()
        df['hour'] = df['date'].dt.hour
        
        analysis = {
            'total_spending': df['total'].sum(),
            'average_receipt': df['total'].mean(),
            'median_receipt': df['total'].median(),
            'spending_by_day': df.groupby('day_of_week')['total'].sum().to_dict(),
            'spending_by_month': df.groupby('month')['total'].sum().to_dict(),
            'spending_by_category': df.groupby('category')['total'].sum().to_dict(),
            'most_frequent_stores': df['store_name'].value_counts().head(5).to_dict(),
            'receipt_frequency': len(df),
            'date_range': {
                'start': df['date'].min().isoformat(),
                'end': df['date'].max().isoformat()
            }
        }
        
        return analysis
    
    def detect_spending_anomalies(self, receipts: List[Dict[str, Any]], threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect unusual spending patterns"""
        if not receipts:
            return []
        
        df = pd.DataFrame(receipts)
        
        # Calculate z-scores for spending amounts
        mean_spending = df['total'].mean()
        std_spending = df['total'].std()
        
        if std_spending == 0:
            return []
        
        df['z_score'] = (df['total'] - mean_spending) / std_spending
        
        # Find anomalies
        anomalies = df[abs(df['z_score']) > threshold]
        
        return anomalies.to_dict('records')
    
    def predict_monthly_spending(self, receipts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Predict spending for the current month based on historical data"""
        if not receipts:
            return {'predicted_total': 0.0, 'confidence': 0.0}
        
        df = pd.DataFrame(receipts)
        df['date'] = pd.to_datetime(df['date'])
        
        # Group by month
        monthly_spending = df.groupby(df['date'].dt.to_period('M'))['total'].sum()
        
        if len(monthly_spending) < 2:
            return {'predicted_total': 0.0, 'confidence': 0.0}
        
        # Simple linear trend prediction
        values = monthly_spending.values
        trend = np.polyfit(range(len(values)), values, 1)
        
        # Predict next month
        predicted = trend[0] * len(values) + trend[1]
        
        # Calculate confidence based on variance
        variance = np.var(values)
        confidence = max(0, 1 - (variance / (predicted ** 2)) if predicted != 0 else 0)
        
        return {
            'predicted_total': max(0, predicted),
            'confidence': min(1.0, confidence)
        }
    
    def cluster_spending_behavior(self, receipts: List[Dict[str, Any]], n_clusters: int = 3) -> Dict[str, Any]:
        """Cluster receipts by spending behavior"""
        if not receipts or len(receipts) < n_clusters:
            return {}
        
        df = pd.DataFrame(receipts)
        df['date'] = pd.to_datetime(df['date'])
        
        # Create features for clustering
        features = []
        for _, receipt in df.iterrows():
            feature_vector = [
                receipt['total'],
                receipt['date'].weekday(),  # Day of week
                receipt['date'].hour if 'hour' in receipt else 12,  # Hour of day
                len(receipt.get('items', [])),  # Number of items
            ]
            features.append(feature_vector)
        
        features_array = np.array(features)
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features_array)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)
        
        # Analyze clusters
        df['cluster'] = clusters
        cluster_analysis = {}
        
        for i in range(n_clusters):
            cluster_data = df[df['cluster'] == i]
            cluster_analysis[f'cluster_{i}'] = {
                'size': len(cluster_data),
                'avg_spending': cluster_data['total'].mean(),
                'common_stores': cluster_data['store_name'].value_counts().head(3).to_dict(),
                'common_categories': cluster_data['category'].value_counts().head(3).to_dict(),
                'description': self._describe_cluster(cluster_data)
            }
        
        return cluster_analysis
    
    def _describe_cluster(self, cluster_data: pd.DataFrame) -> str:
        """Generate a description for a spending cluster"""
        avg_total = cluster_data['total'].mean()
        most_common_store = cluster_data['store_name'].mode().iloc[0] if not cluster_data['store_name'].mode().empty else 'Various'
        most_common_category = cluster_data['category'].mode().iloc[0] if not cluster_data['category'].mode().empty else 'Mixed'
        
        if avg_total < 20:
            spending_level = "low"
        elif avg_total < 100:
            spending_level = "medium"
        else:
            spending_level = "high"
        
        return f"{spending_level.title()} spending cluster, primarily at {most_common_store} for {most_common_category} purchases"
    
    def calculate_savings_opportunities(self, receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify potential savings opportunities"""
        if not receipts:
            return {}
        
        df = pd.DataFrame(receipts)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate monthly spending by category
        monthly_category_spending = df.groupby([
            df['date'].dt.to_period('M'), 
            'category'
        ])['total'].sum().unstack(fill_value=0)
        
        opportunities = {}
        
        # Find categories with increasing spending
        for category in monthly_category_spending.columns:
            values = monthly_category_spending[category].values
            if len(values) >= 3:
                # Check if spending is increasing
                trend = np.polyfit(range(len(values)), values, 1)[0]
                if trend > 0:
                    current_monthly = values[-1]
                    potential_savings = trend * 12  # Annual increase
                    opportunities[category] = {
                        'monthly_spending': current_monthly,
                        'increasing_trend': trend,
                        'potential_annual_savings': potential_savings,
                        'recommendation': f"Consider budgeting for {category} - spending is increasing by ${trend:.2f}/month"
                    }
        
        return opportunities
    
    def generate_spending_insights(self, receipts: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights from spending data"""
        insights = []
        
        if not receipts:
            return ["No receipt data available for analysis."]
        
        df = pd.DataFrame(receipts)
        df['date'] = pd.to_datetime(df['date'])
        
        # Insight 1: Most expensive category
        category_spending = df.groupby('category')['total'].sum()
        top_category = category_spending.idxmax()
        top_amount = category_spending.max()
        insights.append(f"Your highest spending category is {top_category} with ${top_amount:.2f} total.")
        
        # Insight 2: Shopping frequency
        days_between_receipts = df['date'].diff().dt.days.mean()
        if not pd.isna(days_between_receipts):
            insights.append(f"You shop approximately every {days_between_receipts:.1f} days.")
        
        # Insight 3: Weekend vs weekday spending
        df['is_weekend'] = df['date'].dt.weekday >= 5
        weekend_avg = df[df['is_weekend']]['total'].mean()
        weekday_avg = df[~df['is_weekend']]['total'].mean()
        
        if weekend_avg > weekday_avg * 1.2:
            insights.append(f"You spend {((weekend_avg/weekday_avg - 1) * 100):.0f}% more on weekends.")
        elif weekday_avg > weekend_avg * 1.2:
            insights.append(f"You spend {((weekday_avg/weekend_avg - 1) * 100):.0f}% more on weekdays.")
        
        # Insight 4: Store loyalty
        store_counts = df['store_name'].value_counts()
        if len(store_counts) > 1:
            top_store = store_counts.index[0]
            store_percentage = (store_counts.iloc[0] / len(df)) * 100
            insights.append(f"You shop most frequently at {top_store} ({store_percentage:.0f}% of receipts).")
        
        return insights
