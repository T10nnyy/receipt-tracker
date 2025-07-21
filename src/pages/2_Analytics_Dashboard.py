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
from datetime import datetime, timedelta
import numpy as np
import logging
from collections import defaultdict

from core.database import DatabaseManager
from core.algorithms import ReceiptAnalyzer

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Analytics Dashboard - Receipt Processor",
    page_icon="📊",
    layout="wide"
)

# Initialize components
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = ReceiptAnalyzer()

def main():
    st.title("📊 Analytics Dashboard")
    st.markdown("Comprehensive insights into your spending patterns")
    
    try:
        receipts = st.session_state.db_manager.get_all_receipts()
        
        if not receipts:
            st.info("📝 No receipts found. Upload some receipts first!")
            if st.button("Go to Upload Page"):
                st.switch_page("src/app.py")
            return
        
        # Generate analytics
        analytics = st.session_state.analyzer.generate_analytics(receipts)
        
        # Time period selector
        col1, col2 = st.columns([3, 1])
        with col2:
            time_period = st.selectbox(
                "📅 Time Period",
                ["All Time", "Last 30 Days", "Last 90 Days", "Last Year"],
                index=0
            )
        
        # Filter receipts based on time period
        filtered_receipts = filter_by_time_period(receipts, time_period)
        
        if time_period != "All Time":
            analytics = st.session_state.analyzer.generate_analytics(filtered_receipts)
        
        # Key Metrics Row
        display_key_metrics(analytics)
        
        st.divider()
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            display_spending_over_time(filtered_receipts)
        
        with col2:
            display_top_merchants(analytics)
        
        st.divider()
        
        # Charts Row 2
        col1, col2 = st.columns(2)
        
        with col1:
            display_category_breakdown(filtered_receipts)
        
        with col2:
            display_monthly_trends(analytics)
        
        st.divider()
        
        # Advanced Analytics
        col1, col2 = st.columns(2)
        
        with col1:
            display_spending_patterns(filtered_receipts)
        
        with col2:
            display_insights_and_patterns(filtered_receipts)
        
        st.divider()
        
        # Detailed Tables
        display_detailed_analytics(analytics, filtered_receipts)
    
    except Exception as e:
        logger.error(f"Error in analytics dashboard: {e}")
        st.error(f"❌ Error generating analytics: {str(e)}")

def filter_by_time_period(receipts, period):
    """Filter receipts based on selected time period"""
    if period == "All Time":
        return receipts
    
    now = datetime.now()
    
    if period == "Last 30 Days":
        cutoff = now - timedelta(days=30)
    elif period == "Last 90 Days":
        cutoff = now - timedelta(days=90)
    elif period == "Last Year":
        cutoff = now - timedelta(days=365)
    else:
        return receipts
    
    return [r for r in receipts if r.receipt_date and r.receipt_date >= cutoff]

def display_key_metrics(analytics):
    """Display key metrics in a row of columns"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total Receipts",
            analytics['total_receipts'],
            delta=f"+{analytics.get('receipts_this_month', 0)} this month"
        )
    
    with col2:
        st.metric(
            "💰 Total Spent",
            f"${analytics['total_amount']:.2f}",
            delta=f"${analytics.get('amount_this_month', 0):.2f} this month"
        )
    
    with col3:
        st.metric(
            "📈 Average Receipt",
            f"${analytics['average_amount']:.2f}"
        )
    
    with col4:
        st.metric(
            "🏪 Unique Merchants",
            analytics['unique_merchants']
        )

def display_spending_over_time(receipts):
    """Display spending over time chart"""
    st.subheader("📈 Spending Over Time")
    
    # Prepare data
    daily_spending = defaultdict(float)
    for receipt in receipts:
        if receipt.receipt_date and receipt.total_amount:
            date_str = receipt.receipt_date.strftime('%Y-%m-%d')
            daily_spending[date_str] += receipt.total_amount
    
    if not daily_spending:
        st.info("No spending data available for the selected period")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {'Date': date, 'Amount': amount}
        for date, amount in sorted(daily_spending.items())
    ])
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create chart
    fig = px.line(
        df, 
        x='Date', 
        y='Amount',
        title="Daily Spending",
        labels={'Amount': 'Amount ($)', 'Date': 'Date'}
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_top_merchants(analytics):
    """Display top merchants chart"""
    st.subheader("🏪 Top Merchants")
    
    top_merchants = analytics.get('top_merchants', {})
    
    if not top_merchants:
        st.info("No merchant data available")
        return
    
    # Prepare data
    merchants = list(top_merchants.keys())[:10]  # Top 10
    amounts = [top_merchants[m] for m in merchants]
    
    # Create horizontal bar chart
    fig = px.bar(
        x=amounts,
        y=merchants,
        orientation='h',
        title="Spending by Merchant",
        labels={'x': 'Amount ($)', 'y': 'Merchant'}
    )
    
    fig.update_layout(
        xaxis_title="Amount ($)",
        yaxis_title="Merchant",
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_category_breakdown(receipts):
    """Display category breakdown pie chart"""
    st.subheader("📂 Category Breakdown")
    
    # Calculate category spending
    category_spending = defaultdict(float)
    uncategorized_amount = 0
    
    for receipt in receipts:
        if receipt.total_amount:
            if receipt.category:
                category_spending[receipt.category] += receipt.total_amount
            else:
                uncategorized_amount += receipt.total_amount
    
    if uncategorized_amount > 0:
        category_spending['Uncategorized'] = uncategorized_amount
    
    if not category_spending:
        st.info("No category data available")
        return
    
    # Create pie chart
    fig = px.pie(
        values=list(category_spending.values()),
        names=list(category_spending.keys()),
        title="Spending by Category"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    st.plotly_chart(fig, use_container_width=True)

def display_monthly_trends(analytics):
    """Display monthly spending trends"""
    st.subheader("📅 Monthly Trends")
    
    monthly_data = analytics.get('monthly_breakdown', [])
    
    if not monthly_data:
        st.info("No monthly data available")
        return
    
    # Prepare data
    df = pd.DataFrame(monthly_data)
    df = df.sort_values('month')
    
    # Create chart with dual y-axis
    fig = go.Figure()
    
    # Add spending amount bars
    fig.add_trace(go.Bar(
        x=df['month'],
        y=df['total'],
        name='Total Spending',
        yaxis='y',
        marker_color='lightblue'
    ))
    
    # Add receipt count line
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=df['count'],
        mode='lines+markers',
        name='Receipt Count',
        yaxis='y2',
        line=dict(color='red', width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title='Monthly Spending and Receipt Count',
        xaxis_title='Month',
        yaxis=dict(
            title='Amount ($)',
            side='left'
        ),
        yaxis2=dict(
            title='Receipt Count',
            side='right',
            overlaying='y'
        ),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_spending_patterns(receipts):
    """Display spending patterns analysis"""
    st.subheader("🔍 Spending Patterns")
    
    # Day of week analysis
    dow_spending = defaultdict(float)
    dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for receipt in receipts:
        if receipt.receipt_date and receipt.total_amount:
            dow = receipt.receipt_date.weekday()
            dow_spending[dow_names[dow]] += receipt.total_amount
    
    if dow_spending:
        # Create bar chart
        fig = px.bar(
            x=list(dow_spending.keys()),
            y=list(dow_spending.values()),
            title="Spending by Day of Week",
            labels={'x': 'Day of Week', 'y': 'Amount ($)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No day-of-week data available")
    
    # Hour of day analysis (if timestamp available)
    hour_spending = defaultdict(float)
    hour_count = defaultdict(int)
    
    for receipt in receipts:
        if receipt.receipt_date and receipt.total_amount:
            hour = receipt.receipt_date.hour
            hour_spending[hour] += receipt.total_amount
            hour_count[hour] += 1
    
    if hour_spending:
        hours = sorted(hour_spending.keys())
        amounts = [hour_spending[h] for h in hours]
        
        fig = px.bar(
            x=hours,
            y=amounts,
            title="Spending by Hour of Day",
            labels={'x': 'Hour', 'y': 'Amount ($)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)

def display_insights_and_patterns(receipts):
    """Display AI-generated insights and patterns"""
    st.subheader("🧠 AI Insights")
    
    patterns = st.session_state.analyzer.detect_patterns(receipts)
    
    if patterns:
        for pattern in patterns:
            # Color code based on pattern type
            if pattern['type'] in ['high_spending', 'increasing_spending']:
                st.warning(f"⚠️ {pattern['description']}")
            elif pattern['type'] in ['decreasing_spending']:
                st.success(f"✅ {pattern['description']}")
            else:
                st.info(f"💡 {pattern['description']}")
    else:
        st.info("🔍 No significant patterns detected yet. Upload more receipts for better insights!")
    
    # Additional insights
    if len(receipts) >= 5:
        st.subheader("📊 Quick Stats")
        
        # Most expensive receipt
        most_expensive = max(receipts, key=lambda r: r.total_amount or 0)
        if most_expensive.total_amount:
            st.write(f"💸 **Most expensive receipt:** ${most_expensive.total_amount:.2f} at {most_expensive.merchant_name or 'Unknown'}")
        
        # Most frequent merchant
        merchant_counts = defaultdict(int)
        for receipt in receipts:
            if receipt.merchant_name:
                merchant_counts[receipt.merchant_name] += 1
        
        if merchant_counts:
            most_frequent_merchant = max(merchant_counts, key=merchant_counts.get)
            st.write(f"🏪 **Most frequent merchant:** {most_frequent_merchant} ({merchant_counts[most_frequent_merchant]} visits)")
        
        # Average days between receipts
        dates = [r.receipt_date for r in receipts if r.receipt_date]
        if len(dates) >= 2:
            dates.sort()
            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            avg_interval = sum(intervals) / len(intervals)
            st.write(f"📅 **Average days between receipts:** {avg_interval:.1f} days")

def display_detailed_analytics(analytics, receipts):
    """Display detailed analytics tables"""
    st.subheader("📋 Detailed Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Monthly Summary", "Merchant Analysis", "Category Analysis"])
    
    with tab1:
        if analytics.get('monthly_breakdown'):
            df = pd.DataFrame(analytics['monthly_breakdown'])
            df['average'] = df['average'].round(2)
            df['total'] = df['total'].round(2)
            df.columns = ['Month', 'Receipt Count', 'Total Spent', 'Average per Receipt']
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No monthly data available")
    
    with tab2:
        top_merchants = analytics.get('top_merchants', {})
        if top_merchants:
            merchant_data = []
            for merchant, amount in top_merchants.items():
                receipt_count = sum(1 for r in receipts if r.merchant_name == merchant)
                avg_amount = amount / receipt_count if receipt_count > 0 else 0
                merchant_data.append({
                    'Merchant': merchant,
                    'Total Spent': f"${amount:.2f}",
                    'Receipt Count': receipt_count,
                    'Average per Visit': f"${avg_amount:.2f}"
                })
            
            df = pd.DataFrame(merchant_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No merchant data available")
    
    with tab3:
        # Category analysis
        category_data = defaultdict(lambda: {'total': 0, 'count': 0})
        
        for receipt in receipts:
            if receipt.total_amount:
                category = receipt.category or 'Uncategorized'
                category_data[category]['total'] += receipt.total_amount
                category_data[category]['count'] += 1
        
        if category_data:
            cat_list = []
            for category, data in category_data.items():
                avg_amount = data['total'] / data['count'] if data['count'] > 0 else 0
                cat_list.append({
                    'Category': category,
                    'Total Spent': f"${data['total']:.2f}",
                    'Receipt Count': data['count'],
                    'Average per Receipt': f"${avg_amount:.2f}"
                })
            
            df = pd.DataFrame(cat_list)
            df = df.sort_values('Total Spent', ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No category data available")

if __name__ == "__main__":
    main()
