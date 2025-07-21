"""
Analytics Dashboard Page - Comprehensive Receipt Analytics

This page provides advanced analytics and visualizations for receipt data including
spending trends, vendor analysis, category breakdowns, and pattern detection.
Features interactive charts, statistical insights, and anomaly detection.

Author: Receipt Processing Team
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import calendar

# Import core modules
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from core.database import DatabaseManager
from core.algorithms import ReceiptAnalyzer
from core.models import CategoryEnum, CurrencyEnum
from ui.components import apply_custom_css, create_sidebar

# Configure page
st.set_page_config(
    page_title="Analytics Dashboard - Receipt Processing",
    page_icon="📊",
    layout="wide"
)

def load_receipt_data():
    """Load receipt data from database."""
    try:
        db_manager = DatabaseManager()
        receipts = db_manager.get_all_receipts()
        return receipts
    except Exception as e:
        st.error(f"Failed to load receipt data: {e}")
        return []

def show_overview_metrics(receipts, analytics):
    """Display key overview metrics."""
    st.subheader("📈 Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Receipts",
            analytics.total_receipts,
            help="Total number of processed receipts"
        )
    
    with col2:
        st.metric(
            "Total Spending",
            f"${analytics.total_amount:,.2f}",
            help="Total amount across all receipts"
        )
    
    with col3:
        st.metric(
            "Average Amount",
            f"${analytics.average_amount:.2f}",
            help="Average transaction amount"
        )
    
    with col4:
        unique_vendors = len(analytics.vendor_stats)
        st.metric(
            "Unique Vendors",
            unique_vendors,
            help="Number of different vendors"
        )
    
    with col5:
        if receipts:
            date_range = (max(r.transaction_date for r in receipts) - 
                         min(r.transaction_date for r in receipts)).days
            st.metric(
                "Date Range",
                f"{date_range} days",
                help="Time span of receipt data"
            )

def show_spending_analysis(analytics):
    """Display detailed spending analysis charts."""
    st.subheader("💰 Spending Analysis")
    
    # Vendor analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏪 Top Vendors by Spending")
        
        if analytics.vendor_stats:
            # Prepare vendor data
            vendor_data = []
            for vendor, stats in analytics.vendor_stats.items():
                vendor_data.append({
                    'vendor': vendor,
                    'total_amount': float(stats['total_amount']),
                    'count': stats['count'],
                    'avg_amount': float(stats['average_amount'])
                })
            
            # Sort by total amount and take top 10
            vendor_data.sort(key=lambda x: x['total_amount'], reverse=True)
            top_vendors = vendor_data[:10]
            
            if top_vendors:
                vendors_df = pd.DataFrame(top_vendors)
                
                fig = px.bar(
                    vendors_df,
                    x='total_amount',
                    y='vendor',
                    orientation='h',
                    title="Total Spending by Vendor",
                    labels={'total_amount': 'Total Amount ($)', 'vendor': 'Vendor'},
                    color='total_amount',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No vendor data available")
        else:
            st.info("No vendor data available")
    
    with col2:
        st.markdown("#### 🏷️ Spending by Category")
        
        if analytics.category_stats:
            # Prepare category data
            category_data = []
            for category, stats in analytics.category_stats.items():
                category_data.append({
                    'category': category.title(),
                    'total_amount': float(stats['total_amount']),
                    'count': stats['count'],
                    'percentage': stats['percentage']
                })
            
            if category_data:
                categories_df = pd.DataFrame(category_data)
                
                fig = px.pie(
                    categories_df,
                    values='total_amount',
                    names='category',
                    title="Spending Distribution by Category",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")
        else:
            st.info("No category data available")

def show_time_trends(analytics, receipts):
    """Display time-based spending trends."""
    st.subheader("📅 Time Trends")
    
    if not receipts:
        st.info("No receipt data available for trend analysis")
        return
    
    # Monthly trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Monthly Spending Trend")
        
        if analytics.monthly_stats:
            # Prepare monthly data
            monthly_data = []
            for month, stats in analytics.monthly_stats.items():
                monthly_data.append({
                    'month': month,
                    'total_amount': float(stats['total_amount']),
                    'count': stats['count'],
                    'avg_amount': float(stats['average_amount'])
                })
            
            # Sort by month
            monthly_data.sort(key=lambda x: x['month'])
            
            if monthly_data:
                monthly_df = pd.DataFrame(monthly_data)
                
                fig = go.Figure()
                
                # Add spending line
                fig.add_trace(go.Scatter(
                    x=monthly_df['month'],
                    y=monthly_df['total_amount'],
                    mode='lines+markers',
                    name='Total Spending',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="Monthly Spending Trend",
                    xaxis_title="Month",
                    yaxis_title="Amount ($)",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly data available")
        else:
            st.info("No monthly data available")
    
    with col2:
        st.markdown("#### 📊 Transaction Count by Month")
        
        if analytics.monthly_stats:
            monthly_data = []
            for month, stats in analytics.monthly_stats.items():
                monthly_data.append({
                    'month': month,
                    'count': stats['count']
                })
            
            monthly_data.sort(key=lambda x: x['month'])
            
            if monthly_data:
                monthly_df = pd.DataFrame(monthly_data)
                
                fig = px.bar(
                    monthly_df,
                    x='month',
                    y='count',
                    title="Transaction Count by Month",
                    labels={'count': 'Number of Transactions', 'month': 'Month'},
                    color='count',
                    color_continuous_scale='Greens'
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly transaction data available")
        else:
            st.info("No monthly transaction data available")
    
    # Day of week analysis
    st.markdown("#### 📅 Spending Patterns by Day of Week")
    
    if analytics.spending_patterns and 'day_patterns' in analytics.spending_patterns:
        day_data = []
        for day, stats in analytics.spending_patterns['day_patterns'].items():
            day_data.append({
                'day': day,
                'total_amount': float(stats['total_amount']),
                'count': stats['count']
            })
        
        if day_data:
            # Order days properly
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_data.sort(key=lambda x: day_order.index(x['day']) if x['day'] in day_order else 7)
            
            days_df = pd.DataFrame(day_data)
            
            fig = px.bar(
                days_df,
                x='day',
                y='total_amount',
                title="Spending by Day of Week",
                labels={'total_amount': 'Total Amount ($)', 'day': 'Day of Week'},
                color='total_amount',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No day-of-week data available")
    else:
        st.info("No day-of-week data available")

def show_advanced_insights(analytics, receipts):
    """Display advanced analytics and insights."""
    st.subheader("🔍 Advanced Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚨 Anomaly Detection")
        
        if analytics.anomalies:
            st.warning(f"Found {len(analytics.anomalies)} potential anomalies")
            
            anomaly_data = []
            for anomaly in analytics.anomalies[:10]:  # Show top 10
                anomaly_data.append({
                    'Type': anomaly['type'].replace('_', ' ').title(),
                    'Vendor': anomaly['vendor'],
                    'Amount': f"${anomaly['amount']}",
                    'Date': anomaly['date'].strftime('%Y-%m-%d') if hasattr(anomaly['date'], 'strftime') else str(anomaly['date'])
                })
            
            if anomaly_data:
                anomalies_df = pd.DataFrame(anomaly_data)
                st.dataframe(anomalies_df, use_container_width=True, hide_index=True)
            
        else:
            st.success("No anomalies detected in your spending patterns")
    
    with col2:
        st.markdown("#### 🎯 Vendor Loyalty Analysis")
        
        if analytics.spending_patterns:
            loyalty_score = analytics.spending_patterns.get('vendor_loyalty_score', 0)
            unique_vendors = analytics.spending_patterns.get('unique_vendors', 0)
            repeat_vendors = analytics.spending_patterns.get('repeat_vendors', 0)
            
            st.metric("Loyalty Score", f"{loyalty_score:.1%}", help="Percentage of vendors visited multiple times")
            st.metric("Unique Vendors", unique_vendors)
            st.metric("Repeat Vendors", repeat_vendors)
            
            # Vendor frequency distribution
            if analytics.vendor_stats:
                frequency_data = defaultdict(int)
                for vendor, stats in analytics.vendor_stats.items():
                    count = stats['count']
                    if count == 1:
                        frequency_data['1 visit'] += 1
                    elif count <= 3:
                        frequency_data['2-3 visits'] += 1
                    elif count <= 5:
                        frequency_data['4-5 visits'] += 1
                    else:
                        frequency_data['6+ visits'] += 1
                
                if frequency_data:
                    freq_df = pd.DataFrame(list(frequency_data.items()), columns=['Frequency', 'Count'])
                    
                    fig = px.bar(
                        freq_df,
                        x='Frequency',
                        y='Count',
                        title="Vendor Visit Frequency",
                        color='Count',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No loyalty data available")

def show_currency_analysis(analytics):
    """Display currency distribution analysis."""
    if not analytics.currency_stats or len(analytics.currency_stats) <= 1:
        return
    
    st.subheader("💱 Currency Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Currency Distribution")
        
        currency_data = []
        for currency, stats in analytics.currency_stats.items():
            currency_data.append({
                'currency': currency,
                'count': stats['count'],
                'percentage': stats['percentage']
            })
        
        if currency_data:
            currency_df = pd.DataFrame(currency_data)
            
            fig = px.pie(
                currency_df,
                values='count',
                names='currency',
                title="Receipts by Currency",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Currency Statistics")
        
        for currency, stats in analytics.currency_stats.items():
            st.metric(
                f"{currency} Transactions",
                stats['count'],
                f"{stats['percentage']:.1f}% of total"
            )

def show_export_options(receipts):
    """Display data export options."""
    st.subheader("📤 Export Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Summary Report"):
            export_summary_report(receipts)
    
    with col2:
        if st.button("📈 Export Trend Data"):
            export_trend_data(receipts)
    
    with col3:
        if st.button("🏪 Export Vendor Analysis"):
            export_vendor_analysis(receipts)

def export_summary_report(receipts):
    """Export comprehensive summary report."""
    try:
        analyzer = ReceiptAnalyzer()
        analytics = analyzer.generate_analytics(receipts)
        
        # Create summary data
        summary_data = {
            'Total Receipts': analytics.total_receipts,
            'Total Amount': str(analytics.total_amount),
            'Average Amount': str(analytics.average_amount),
            'Median Amount': str(analytics.median_amount),
            'Unique Vendors': len(analytics.vendor_stats),
            'Unique Categories': len(analytics.category_stats),
            'Date Range': f"{min(r.transaction_date for r in receipts).date()} to {max(r.transaction_date for r in receipts).date()}" if receipts else "N/A"
        }
        
        # Convert to DataFrame and CSV
        summary_df = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
        csv_string = summary_df.to_csv(index=False)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            label="📥 Download Summary Report",
            data=csv_string,
            file_name=f"receipt_summary_{timestamp}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Export failed: {e}")

def export_trend_data(receipts):
    """Export monthly trend data."""
    try:
        # Group by month
        monthly_data = defaultdict(lambda: {'count': 0, 'total_amount': Decimal('0.00')})
        
        for receipt in receipts:
            month_key =receipt.transaction_date.strftime('%Y-%m')
            monthly_data[month_key]['count'] += 1
            monthly_data[month_key]['total_amount'] += receipt.amount
        
        # Convert to DataFrame
        trend_data = []
        for month, stats in monthly_data.items():
            trend_data.append({
                'Month': month,
                'Transaction Count': stats['count'],
                'Total Amount': str(stats['total_amount']),
                'Average Amount': str(stats['total_amount'] / stats['count'])
            })
        
        trend_df = pd.DataFrame(trend_data)
        trend_df = trend_df.sort_values('Month')
        csv_string = trend_df.to_csv(index=False)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            label="📥 Download Trend Data",
            data=csv_string,
            file_name=f"receipt_trends_{timestamp}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Export failed: {e}")

def export_vendor_analysis(receipts):
    """Export vendor analysis data."""
    try:
        analyzer = ReceiptAnalyzer()
        analytics = analyzer.generate_analytics(receipts)
        
        # Convert vendor stats to DataFrame
        vendor_data = []
        for vendor, stats in analytics.vendor_stats.items():
            vendor_data.append({
                'Vendor': vendor,
                'Transaction Count': stats['count'],
                'Total Amount': str(stats['total_amount']),
                'Average Amount': str(stats['average_amount']),
                'Last Visit': stats['last_visit'].strftime('%Y-%m-%d') if stats['last_visit'] else 'N/A',
                'Frequency Score': f"{stats['frequency_score']:.3f}"
            })
        
        vendor_df = pd.DataFrame(vendor_data)
        vendor_df = vendor_df.sort_values('Total Amount', key=lambda x: x.str.replace('$', '').astype(float), ascending=False)
        csv_string = vendor_df.to_csv(index=False)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            label="📥 Download Vendor Analysis",
            data=csv_string,
            file_name=f"vendor_analysis_{timestamp}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Export failed: {e}")

def main():
    """Main dashboard function."""
    # Apply styling
    apply_custom_css()
    
    # Create sidebar
    create_sidebar()
    
    # Page header
    st.title("📊 Analytics Dashboard")
    st.markdown("Comprehensive insights into your receipt data and spending patterns")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading receipt data..."):
        receipts = load_receipt_data()
    
    if not receipts:
        st.warning("No receipt data found. Please upload some receipts first!")
        if st.button("📤 Go to Data Explorer"):
            st.switch_page("pages/1_Data_Explorer.py")
        return
    
    # Generate analytics
    with st.spinner("Generating analytics..."):
        analyzer = ReceiptAnalyzer()
        analytics = analyzer.generate_analytics(receipts)
    
    # Display analytics sections
    show_overview_metrics(receipts, analytics)
    st.markdown("---")
    
    show_spending_analysis(analytics)
    st.markdown("---")
    
    show_time_trends(analytics, receipts)
    st.markdown("---")
    
    show_advanced_insights(analytics, receipts)
    st.markdown("---")
    
    show_currency_analysis(analytics)
    st.markdown("---")
    
    show_export_options(receipts)

if __name__ == "__main__":
    main()
