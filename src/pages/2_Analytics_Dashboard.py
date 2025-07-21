"""
Analytics Dashboard page for receipt insights and visualizations.
Provides comprehensive analytics, trends, and spending patterns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
from collections import defaultdict
import calendar

from ..core.database import ReceiptDatabase
from ..core.algorithms import ReceiptAnalyzer
from ..ui.components import UIComponents

# Page configuration
st.set_page_config(
    page_title="Analytics Dashboard - Receipt Processor",
    page_icon="📊",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state for analytics."""
    if 'db' not in st.session_state:
        st.session_state.db = ReceiptDatabase()
    
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ReceiptAnalyzer()


def main():
    """Main analytics dashboard function."""
    initialize_session_state()
    
    st.title("📊 Analytics Dashboard")
    st.markdown("Comprehensive insights into your spending patterns and receipt data")
    
    try:
        # Load data
        all_receipts = st.session_state.db.get_all_receipts()
        
        if not all_receipts:
            st.info("📝 No receipts found. Upload some receipts to see analytics!")
            return
        
        # Generate analytics
        analytics_data = st.session_state.analyzer.generate_analytics(all_receipts)
        
        # Create tabs for different analytics views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Overview", 
            "💰 Spending Analysis", 
            "📅 Time Trends", 
            "🔍 Advanced Insights"
        ])
        
        with tab1:
            render_overview_tab(analytics_data, all_receipts)
        
        with tab2:
            render_spending_analysis_tab(all_receipts)
        
        with tab3:
            render_time_trends_tab(all_receipts)
        
        with tab4:
            render_advanced_insights_tab(all_receipts)
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")


def render_overview_tab(analytics_data, receipts):
    """Render overview analytics tab."""
    st.header("📈 Spending Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Receipts",
            analytics_data.total_receipts,
            help="Total number of processed receipts"
        )
    
    with col2:
        st.metric(
            "Total Spent",
            f"${analytics_data.total_amount:,.2f}",
            help="Sum of all receipt amounts"
        )
    
    with col3:
        st.metric(
            "Average Amount",
            f"${analytics_data.average_amount:.2f}",
            help="Average amount per receipt"
        )
    
    with col4:
        if analytics_data.date_range:
            days = (analytics_data.date_range[1] - analytics_data.date_range[0]).days
            st.metric("Date Range", f"{days} days", help="Time span of receipts")
    
    # Quick insights
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Top vendors chart
        if analytics_data.top_vendors:
            st.subheader("🏪 Top Vendors by Spending")
            
            vendors_df = pd.DataFrame(analytics_data.top_vendors[:8])
            fig = px.bar(
                vendors_df,
                x='total_amount',
                y='vendor',
                orientation='h',
                title="Top 8 Vendors",
                labels={'total_amount': 'Total Amount ($)', 'vendor': 'Vendor'},
                color='total_amount',
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Category breakdown
        if analytics_data.category_breakdown:
            st.subheader("🏷️ Spending by Category")
            
            categories_df = pd.DataFrame(analytics_data.category_breakdown)
            fig = px.pie(
                categories_df,
                values='total_amount',
                names='category',
                title="Category Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Monthly trends overview
    if analytics_data.monthly_trends:
        st.markdown("---")
        st.subheader("📅 Monthly Spending Trend")
        
        trends_df = pd.DataFrame(analytics_data.monthly_trends)
        trends_df = trends_df.sort_values('month')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trends_df['month'],
            y=trends_df['total_amount'],
            mode='lines+markers',
            name='Monthly Spending',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8, color='#1f77b4'),
            fill='tonexty',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))
        
        fig.update_layout(
            title="Monthly Spending Trend",
            xaxis_title="Month",
            yaxis_title="Total Amount ($)",
            height=400,
            showlegend=False,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.markdown("---")
    st.subheader("📋 Recent Activity")
    
    recent_receipts = sorted(receipts, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
    
    for receipt in recent_receipts:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{receipt.vendor}**")
            
            with col2:
                st.write(f"${receipt.amount}")
            
            with col3:
                st.write(f"{receipt.transaction_date}")
            
            with col4:
                st.write(f"{receipt.category}")


def render_spending_analysis_tab(receipts):
    """Render detailed spending analysis."""
    st.header("💰 Spending Analysis")
    
    # Time period selector
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_period = st.selectbox(
            "Analysis Period",
            options=["All Time", "Last 30 Days", "Last 90 Days", "Last Year", "Custom Range"],
            help="Select time period for analysis"
        )
    
    with col2:
        if analysis_period == "Custom Range":
            date_range = st.date_input(
                "Select Date Range",
                value=(date.today() - timedelta(days=30), date.today()),
                help="Choose custom date range"
            )
        else:
            date_range = None
    
    # Filter receipts based on period
    filtered_receipts = filter_receipts_by_period(receipts, analysis_period, date_range)
    
    if not filtered_receipts:
        st.warning("No receipts found for the selected period.")
        return
    
    st.info(f"Analyzing {len(filtered_receipts)} receipts")
    
    # Spending distribution analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💵 Amount Distribution")
        
        amounts = [float(r.amount) for r in filtered_receipts]
        
        fig = px.histogram(
            x=amounts,
            nbins=20,
            title="Distribution of Receipt Amounts",
            labels={'x': 'Amount ($)', 'y': 'Frequency'},
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        import statistics
        st.write("**Statistics:**")
        st.write(f"• Mean: ${statistics.mean(amounts):.2f}")
        st.write(f"• Median: ${statistics.median(amounts):.2f}")
        st.write(f"• Std Dev: ${statistics.stdev(amounts) if len(amounts) > 1 else 0:.2f}")
        st.write(f"• Min: ${min(amounts):.2f}")
        st.write(f"• Max: ${max(amounts):.2f}")
    
    with col2:
        st.subheader("🏪 Vendor Analysis")
        
        # Vendor frequency and spending
        vendor_stats = defaultdict(lambda: {'count': 0, 'total': 0})
        for receipt in filtered_receipts:
            vendor_stats[receipt.vendor]['count'] += 1
            vendor_stats[receipt.vendor]['total'] += float(receipt.amount)
        
        vendor_df = pd.DataFrame([
            {
                'vendor': vendor,
                'visits': stats['count'],
                'total_spent': stats['total'],
                'avg_per_visit': stats['total'] / stats['count']
            }
            for vendor, stats in vendor_stats.items()
        ]).sort_values('total_spent', ascending=False)
        
        # Top vendors by total spending
        fig = px.bar(
            vendor_df.head(10),
            x='total_spent',
            y='vendor',
            orientation='h',
            title="Top 10 Vendors by Total Spending",
            labels={'total_spent': 'Total Spent ($)', 'vendor': 'Vendor'},
            color='total_spent',
            color_continuous_scale='blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Category deep dive
    st.markdown("---")
    st.subheader("🏷️ Category Deep Dive")
    
    category_stats = defaultdict(lambda: {'count': 0, 'total': 0, 'receipts': []})
    for receipt in filtered_receipts:
        category_stats[receipt.category]['count'] += 1
        category_stats[receipt.category]['total'] += float(receipt.amount)
        category_stats[receipt.category]['receipts'].append(receipt)
    
    # Category comparison
    col1, col2 = st.columns(2)
    
    with col1:
        # Category spending comparison
        category_df = pd.DataFrame([
            {
                'category': category,
                'total_amount': stats['total'],
                'count': stats['count'],
                'avg_amount': stats['total'] / stats['count']
            }
            for category, stats in category_stats.items()
        ])
        
        fig = px.bar(
            category_df.sort_values('total_amount', ascending=True),
            x='total_amount',
            y='category',
            orientation='h',
            title="Spending by Category",
            labels={'total_amount': 'Total Amount ($)', 'category': 'Category'},
            color='total_amount',
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Category frequency vs amount
        fig = px.scatter(
            category_df,
            x='count',
            y='avg_amount',
            size='total_amount',
            color='category',
            title="Category Analysis: Frequency vs Average Amount",
            labels={
                'count': 'Number of Receipts',
                'avg_amount': 'Average Amount ($)',
                'total_amount': 'Total Spent'
            },
            hover_data=['total_amount']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed category breakdown
    st.markdown("---")
    st.subheader("📊 Category Details")
    
    selected_category = st.selectbox(
        "Select Category for Details",
        options=list(category_stats.keys()),
        help="Choose a category to see detailed breakdown"
    )
    
    if selected_category:
        category_receipts = category_stats[selected_category]['receipts']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Receipts", len(category_receipts))
        
        with col2:
            total_spent = sum(float(r.amount) for r in category_receipts)
            st.metric("Total Spent", f"${total_spent:.2f}")
        
        with col3:
            avg_amount = total_spent / len(category_receipts)
            st.metric("Average Amount", f"${avg_amount:.2f}")
        
        # Vendor breakdown within category
        vendor_breakdown = defaultdict(float)
        for receipt in category_receipts:
            vendor_breakdown[receipt.vendor] += float(receipt.amount)
        
        if len(vendor_breakdown) > 1:
            vendor_df = pd.DataFrame([
                {'vendor': vendor, 'amount': amount}
                for vendor, amount in sorted(vendor_breakdown.items(), key=lambda x: x[1], reverse=True)
            ])
            
            fig = px.pie(
                vendor_df.head(8),
                values='amount',
                names='vendor',
                title=f"Vendor Breakdown for {selected_category}",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def render_time_trends_tab(receipts):
    """Render time-based trend analysis."""
    st.header("📅 Time Trends Analysis")
    
    if not receipts:
        st.info("No receipts available for time analysis.")
        return
    
    # Time-based grouping options
    col1, col2 = st.columns(2)
    
    with col1:
        grouping = st.selectbox(
            "Group By",
            options=["Daily", "Weekly", "Monthly", "Quarterly"],
            index=2,
            help="Choose time grouping for analysis"
        )
    
    with col2:
        show_cumulative = st.checkbox("Show Cumulative", help="Display cumulative spending over time")
    
    # Generate time series data
    time_series_data = generate_time_series(receipts, grouping)
    
    if not time_series_data:
        st.warning("Insufficient data for time series analysis.")
        return
    
    # Main time series chart
    st.subheader(f"📈 {grouping} Spending Trends")
    
    df = pd.DataFrame(time_series_data)
    df = df.sort_values('period')
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Spending Amount', 'Number of Receipts'),
        vertical_spacing=0.1
    )
    
    # Amount trend
    if show_cumulative:
        df['cumulative_amount'] = df['total_amount'].cumsum()
        fig.add_trace(
            go.Scatter(
                x=df['period'],
                y=df['cumulative_amount'],
                mode='lines+markers',
                name='Cumulative Amount',
                line=dict(color='#1f77b4', width=3)
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df['period'],
                y=df['total_amount'],
                mode='lines+markers',
                name='Amount',
                line=dict(color='#1f77b4', width=3),
                fill='tonexty'
            ),
            row=1, col=1
        )
    
    # Count trend
    fig.add_trace(
        go.Scatter(
            x=df['period'],
            y=df['count'],
            mode='lines+markers',
            name='Receipt Count',
            line=dict(color='#ff7f0e', width=3)
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(title_text="Time Period", row=2, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Seasonal analysis
    st.markdown("---")
    st.subheader("🌟 Seasonal Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Day of week analysis
        dow_data = defaultdict(lambda: {'count': 0, 'total': 0})
        for receipt in receipts:
            dow = receipt.transaction_date.strftime('%A')
            dow_data[dow]['count'] += 1
            dow_data[dow]['total'] += float(receipt.amount)
        
        dow_df = pd.DataFrame([
            {
                'day': day,
                'avg_amount': stats['total'] / stats['count'],
                'total_amount': stats['total'],
                'count': stats['count']
            }
            for day, stats in dow_data.items()
        ])
        
        # Order by day of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_df['day'] = pd.Categorical(dow_df['day'], categories=day_order, ordered=True)
        dow_df = dow_df.sort_values('day')
        
        fig = px.bar(
            dow_df,
            x='day',
            y='total_amount',
            title="Spending by Day of Week",
            labels={'total_amount': 'Total Amount ($)', 'day': 'Day of Week'},
            color='total_amount',
            color_continuous_scale='blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Monthly pattern (across all years)
        monthly_data = defaultdict(lambda: {'count': 0, 'total': 0})
        for receipt in receipts:
            month = receipt.transaction_date.strftime('%B')
            monthly_data[month]['count'] += 1
            monthly_data[month]['total'] += float(receipt.amount)
        
        monthly_df = pd.DataFrame([
            {
                'month': month,
                'avg_amount': stats['total'] / stats['count'],
                'total_amount': stats['total'],
                'count': stats['count']
            }
            for month, stats in monthly_data.items()
        ])
        
        # Order by month
        month_order = [calendar.month_name[i] for i in range(1, 13)]
        monthly_df['month'] = pd.Categorical(monthly_df['month'], categories=month_order, ordered=True)
        monthly_df = monthly_df.sort_values('month')
        
        fig = px.bar(
            monthly_df,
            x='month',
            y='total_amount',
            title="Spending by Month",
            labels={'total_amount': 'Total Amount ($)', 'month': 'Month'},
            color='total_amount',
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400)
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Trend insights
    st.markdown("---")
    st.subheader("🔍 Trend Insights")
    
    # Calculate trend metrics
    if len(df) >= 2:
        recent_avg = df.tail(3)['total_amount'].mean()
        earlier_avg = df.head(3)['total_amount'].mean()
        trend_direction = "increasing" if recent_avg > earlier_avg else "decreasing"
        trend_percentage = abs((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Trend Direction",
                trend_direction.title(),
                f"{trend_percentage:.1f}%"
            )
        
        with col2:
            peak_period = df.loc[df['total_amount'].idxmax(), 'period']
            peak_amount = df['total_amount'].max()
            st.metric(
                "Peak Spending Period",
                str(peak_period),
                f"${peak_amount:.2f}"
            )
        
        with col3:
            avg_monthly = df['total_amount'].mean()
            st.metric(
                f"Average {grouping} Spending",
                f"${avg_monthly:.2f}"
            )


def render_advanced_insights_tab(receipts):
    """Render advanced analytics and insights."""
    st.header("🔍 Advanced Insights")
    
    if not receipts:
        st.info("No receipts available for advanced analysis.")
        return
    
    # Pattern detection
    patterns = st.session_state.analyzer.detect_spending_patterns(receipts)
    
    # Spending anomalies
    if 'anomalies' in patterns and patterns['anomalies']:
        st.subheader("⚠️ Spending Anomalies")
        st.write("Receipts with unusually high amounts (>2 standard deviations from mean):")
        
        anomalies_df = pd.DataFrame(patterns['anomalies'])
        anomalies_df['amount'] = anomalies_df['amount'].apply(lambda x: f"${x:.2f}")
        anomalies_df['deviation'] = anomalies_df['deviation'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(
            anomalies_df[['vendor', 'amount', 'date', 'deviation']],
            use_container_width=True,
            hide_index=True
        )
    
    # Duplicate detection
    st.markdown("---")
    st.subheader("🔍 Duplicate Detection")
    
    with st.spinner("Analyzing for potential duplicates..."):
        duplicates = st.session_state.analyzer.find_duplicate_receipts(receipts, threshold=0.8)
    
    if duplicates:
        st.warning(f"Found {len(duplicates)} groups of potential duplicates:")
        
        for i, group in enumerate(duplicates, 1):
            with st.expander(f"Duplicate Group {i} ({len(group)} receipts)"):
                for receipt in group:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**ID:** {receipt.id}")
                    
                    with col2:
                        st.write(f"**Vendor:** {receipt.vendor}")
                    
                    with col3:
                        st.write(f"**Amount:** ${receipt.amount}")
                    
                    with col4:
                        st.write(f"**Date:** {receipt.transaction_date}")
    else:
        st.success("✅ No potential duplicates found!")
    
    # Vendor loyalty analysis
    st.markdown("---")
    st.subheader("🏪 Vendor Loyalty Analysis")
    
    vendor_loyalty = defaultdict(lambda: {'visits': 0, 'total_spent': 0, 'first_visit': None, 'last_visit': None})
    
    for receipt in receipts:
        vendor = receipt.vendor
        vendor_loyalty[vendor]['visits'] += 1
        vendor_loyalty[vendor]['total_spent'] += float(receipt.amount)
        
        if vendor_loyalty[vendor]['first_visit'] is None or receipt.transaction_date < vendor_loyalty[vendor]['first_visit']:
            vendor_loyalty[vendor]['first_visit'] = receipt.transaction_date
        
        if vendor_loyalty[vendor]['last_visit'] is None or receipt.transaction_date > vendor_loyalty[vendor]['last_visit']:
            vendor_loyalty[vendor]['last_visit'] = receipt.transaction_date
    
    # Calculate loyalty metrics
    loyalty_df = []
    for vendor, stats in vendor_loyalty.items():
        if stats['visits'] > 1:  # Only include vendors with multiple visits
            days_span = (stats['last_visit'] - stats['first_visit']).days
            loyalty_score = stats['visits'] * stats['total_spent'] / max(days_span, 1)
            
            loyalty_df.append({
                'vendor': vendor,
                'visits': stats['visits'],
                'total_spent': stats['total_spent'],
                'avg_per_visit': stats['total_spent'] / stats['visits'],
                'days_span': days_span,
                'loyalty_score': loyalty_score
            })
    
    if loyalty_df:
        loyalty_df = pd.DataFrame(loyalty_df).sort_values('loyalty_score', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top loyal vendors
            fig = px.bar(
                loyalty_df.head(10),
                x='loyalty_score',
                y='vendor',
                orientation='h',
                title="Vendor Loyalty Score (Visits × Spending ÷ Days)",
                labels={'loyalty_score': 'Loyalty Score', 'vendor': 'Vendor'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Visits vs spending scatter
            fig = px.scatter(
                loyalty_df,
                x='visits',
                y='total_spent',
                size='loyalty_score',
                color='avg_per_visit',
                hover_name='vendor',
                title="Vendor Analysis: Visits vs Total Spending",
                labels={
                    'visits': 'Number of Visits',
                    'total_spent': 'Total Spent ($)',
                    'avg_per_visit': 'Avg per Visit ($)'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Category trends over time
    st.markdown("---")
    st.subheader("📊 Category Trends Analysis")
    
    category_trends = st.session_state.analyzer.calculate_category_trends(receipts, days=90)
    
    if category_trends:
        trends_df = pd.DataFrame([
            {
                'category': category,
                'total_amount': data['total_amount'],
                'avg_daily': data['average_daily'],
                'transaction_count': data['transaction_count']
            }
            for category, data in category_trends.items()
        ]).sort_values('total_amount', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                trends_df,
                x='category',
                y='total_amount',
                title="Category Spending (Last 90 Days)",
                labels={'total_amount': 'Total Amount ($)', 'category': 'Category'}
            )
            fig.update_layout(height=400)
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                trends_df,
                x='transaction_count',
                y='avg_daily',
                size='total_amount',
                color='category',
                title="Category Analysis: Frequency vs Daily Average",
                labels={
                    'transaction_count': 'Number of Transactions',
                    'avg_daily': 'Average Daily Spending ($)'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Insights summary
    st.markdown("---")
    st.subheader("💡 Key Insights")
    
    insights = []
    
    # Top spending category
    if patterns.get('frequent_vendors'):
        top_vendor = patterns['frequent_vendors'][0]
        insights.append(f"🏪 Most frequent vendor: **{top_vendor['vendor']}** ({top_vendor['count']} visits)")
    
    # Spending patterns
    if 'day_of_week' in patterns:
        day_spending = patterns['day_of_week']
        max_day = max(day_spending.keys(), key=lambda x: day_spending[x]['total'])
        insights.append(f"📅 Highest spending day: **{max_day}** (${day_spending[max_day]['total']:.2f})")
    
    # Recent trends
    recent_receipts = [r for r in receipts if (date.today() - r.transaction_date).days <= 30]
    if recent_receipts:
        recent_avg = sum(float(r.amount) for r in recent_receipts) / len(recent_receipts)
        all_avg = sum(float(r.amount) for r in receipts) / len(receipts)
        trend = "higher" if recent_avg > all_avg else "lower"
        insights.append(f"📈 Recent spending trend: **{trend}** than average (${recent_avg:.2f} vs ${all_avg:.2f})")
    
    for insight in insights:
        st.write(f"• {insight}")


def filter_receipts_by_period(receipts, period, custom_range=None):
    """Filter receipts based on time period."""
    today = date.today()
    
    if period == "All Time":
        return receipts
    elif period == "Last 30 Days":
        cutoff = today - timedelta(days=30)
    elif period == "Last 90 Days":
        cutoff = today - timedelta(days=90)
    elif period == "Last Year":
        cutoff = today - timedelta(days=365)
    elif period == "Custom Range" and custom_range:
        if len(custom_range) == 2:
            start_date, end_date = custom_range
            return [r for r in receipts if start_date <= r.transaction_date <= end_date]
        else:
            return receipts
    else:
        return receipts
    
    return [r for r in receipts if r.transaction_date >= cutoff]


def generate_time_series(receipts, grouping):
    """Generate time series data for receipts."""
    time_data = defaultdict(lambda: {'count': 0, 'total_amount': 0})
    
    for receipt in receipts:
        if grouping == "Daily":
            period = receipt.transaction_date
        elif grouping == "Weekly":
            # Get Monday of the week
            days_since_monday = receipt.transaction_date.weekday()
            monday = receipt.transaction_date - timedelta(days=days_since_monday)
            period = monday
        elif grouping == "Monthly":
            period = receipt.transaction_date.replace(day=1)
        elif grouping == "Quarterly":
            quarter = (receipt.transaction_date.month - 1) // 3 + 1
            period = date(receipt.transaction_date.year, (quarter - 1) * 3 + 1, 1)
        else:
            period = receipt.transaction_date
        
        time_data[period]['count'] += 1
        time_data[period]['total_amount'] += float(receipt.amount)
    
    return [
        {
            'period': period,
            'count': data['count'],
            'total_amount': data['total_amount']
        }
        for period, data in time_data.items()
    ]


if __name__ == "__main__":
    main()
