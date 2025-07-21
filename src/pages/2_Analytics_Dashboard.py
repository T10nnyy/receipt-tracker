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
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import ReceiptDatabase
from core.algorithms import ReceiptAnalyzer

# Page configuration
st.set_page_config(
    page_title="Analytics Dashboard - Receipt Processor",
    page_icon="📈",
    layout="wide"
)

# Initialize components
if 'db' not in st.session_state:
    st.session_state.db = ReceiptDatabase()

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = ReceiptAnalyzer()

def main():
    st.title("📈 Analytics Dashboard")
    st.markdown("Advanced analytics and insights for your spending patterns")
    
    try:
        # Load data
        receipts = st.session_state.db.get_all_receipts()
        
        if not receipts:
            st.warning("No receipts found. Please upload some receipts first!")
            return
        
        # Convert to list of dictionaries for analyzer
        receipt_data = [receipt.to_dict() for receipt in receipts]
        df = pd.DataFrame(receipt_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Time period selector
        col1, col2 = st.columns([3, 1])
        with col2:
            time_period = st.selectbox(
                "Analysis Period",
                ["All Time", "Last 30 Days", "Last 90 Days", "Last Year"]
            )
        
        # Filter data based on time period
        if time_period == "Last 30 Days":
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_df = df[df['date'] >= cutoff_date]
        elif time_period == "Last 90 Days":
            cutoff_date = datetime.now() - timedelta(days=90)
            filtered_df = df[df['date'] >= cutoff_date]
        elif time_period == "Last Year":
            cutoff_date = datetime.now() - timedelta(days=365)
            filtered_df = df[df['date'] >= cutoff_date]
        else:
            filtered_df = df
        
        # Convert back to receipt format for analyzer
        filtered_receipt_data = filtered_df.to_dict('records')
        
        # Main dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Patterns", "🔮 Predictions", "💡 Insights"])
        
        with tab1:
            st.header("Spending Overview")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_spent = filtered_df['total'].sum()
            avg_receipt = filtered_df['total'].mean()
            receipt_count = len(filtered_df)
            days_span = (filtered_df['date'].max() - filtered_df['date'].min()).days + 1
            
            with col1:
                st.metric("Total Spent", f"${total_spent:.2f}")
            with col2:
                st.metric("Average Receipt", f"${avg_receipt:.2f}")
            with col3:
                st.metric("Total Receipts", receipt_count)
            with col4:
                st.metric("Daily Average", f"${total_spent/max(days_span, 1):.2f}")
            
            # Spending trend
            st.subheader("Spending Trend")
            daily_spending = filtered_df.groupby(filtered_df['date'].dt.date)['total'].sum().reset_index()
            daily_spending['cumulative'] = daily_spending['total'].cumsum()
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily_spending['date'],
                y=daily_spending['total'],
                mode='lines+markers',
                name='Daily Spending',
                line=dict(color='blue')
            ))
            fig_trend.add_trace(go.Scatter(
                x=daily_spending['date'],
                y=daily_spending['cumulative'],
                mode='lines',
                name='Cumulative Spending',
                yaxis='y2',
                line=dict(color='red', dash='dash')
            ))
            
            fig_trend.update_layout(
                title='Daily and Cumulative Spending',
                xaxis_title='Date',
                yaxis_title='Daily Spending ($)',
                yaxis2=dict(
                    title='Cumulative Spending ($)',
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Category and store breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Spending by Category")
                category_data = filtered_df.groupby('category').agg({
                    'total': ['sum', 'count', 'mean']
                }).round(2)
                category_data.columns = ['Total Spent', 'Receipt Count', 'Avg per Receipt']
                category_data = category_data.sort_values('Total Spent', ascending=False)
                
                # Create pie chart
                fig_cat = px.pie(
                    values=category_data['Total Spent'],
                    names=category_data.index,
                    title='Spending Distribution by Category'
                )
                st.plotly_chart(fig_cat, use_container_width=True)
                
                # Show table
                st.dataframe(category_data, use_container_width=True)
            
            with col2:
                st.subheader("Top Stores")
                store_data = filtered_df.groupby('store_name').agg({
                    'total': ['sum', 'count', 'mean']
                }).round(2)
                store_data.columns = ['Total Spent', 'Visit Count', 'Avg per Visit']
                store_data = store_data.sort_values('Total Spent', ascending=False).head(10)
                
                # Create bar chart
                fig_store = px.bar(
                    x=store_data['Total Spent'],
                    y=store_data.index,
                    orientation='h',
                    title='Top 10 Stores by Spending'
                )
                fig_store.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_store, use_container_width=True)
                
                # Show table
                st.dataframe(store_data, use_container_width=True)
        
        with tab2:
            st.header("Spending Patterns")
            
            # Analyze patterns
            patterns = st.session_state.analyzer.analyze_spending_patterns(filtered_receipt_data)
            
            if patterns:
                # Day of week patterns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Spending by Day of Week")
                    if 'spending_by_day' in patterns:
                        dow_data = patterns['spending_by_day']
                        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        dow_df = pd.DataFrame([
                            {'day': day, 'spending': dow_data.get(day, 0)} 
                            for day in days_order
                        ])
                        
                        fig_dow = px.bar(dow_df, x='day', y='spending', title='Weekly Spending Pattern')
                        st.plotly_chart(fig_dow, use_container_width=True)
                
                with col2:
                    st.subheader("Monthly Spending")
                    if 'spending_by_month' in patterns:
                        month_data = patterns['spending_by_month']
                        month_df = pd.DataFrame([
                            {'month': month, 'spending': amount} 
                            for month, amount in month_data.items()
                        ])
                        
                        fig_month = px.bar(month_df, x='month', y='spending', title='Monthly Spending Pattern')
                        st.plotly_chart(fig_month, use_container_width=True)
                
                # Heatmap of spending patterns
                st.subheader("Spending Heatmap")
                filtered_df['day_of_week'] = filtered_df['date'].dt.day_name()
                filtered_df['hour'] = filtered_df['date'].dt.hour
                
                # Create heatmap data
                heatmap_data = filtered_df.groupby(['day_of_week', 'hour'])['total'].sum().unstack(fill_value=0)
                
                # Reorder days
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                heatmap_data = heatmap_data.reindex(day_order)
                
                fig_heatmap = px.imshow(
                    heatmap_data.values,
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    title='Spending Patterns by Day and Hour',
                    labels={'x': 'Hour of Day', 'y': 'Day of Week', 'color': 'Total Spent ($)'}
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Clustering analysis
                st.subheader("Spending Behavior Clusters")
                clusters = st.session_state.analyzer.cluster_spending_behavior(filtered_receipt_data)
                
                if clusters:
                    for cluster_name, cluster_info in clusters.items():
                        with st.expander(f"Cluster {cluster_name.split('_')[1]} - {cluster_info['description']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Size:** {cluster_info['size']} receipts")
                                st.write(f"**Average Spending:** ${cluster_info['avg_spending']:.2f}")
                            
                            with col2:
                                st.write("**Common Stores:**")
                                for store, count in cluster_info['common_stores'].items():
                                    st.write(f"• {store}: {count} visits")
        
        with tab3:
            st.header("Spending Predictions")
            
            # Monthly prediction
            prediction = st.session_state.analyzer.predict_monthly_spending(filtered_receipt_data)
            
            if prediction and prediction['predicted_total'] > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Predicted Monthly Spending",
                        f"${prediction['predicted_total']:.2f}",
                        help=f"Confidence: {prediction['confidence']:.1%}"
                    )
                
                with col2:
                    confidence_color = "green" if prediction['confidence'] > 0.7 else "orange" if prediction['confidence'] > 0.4 else "red"
                    st.markdown(f"**Prediction Confidence:** :{confidence_color}[{prediction['confidence']:.1%}]")
                
                # Show prediction chart
                monthly_spending = filtered_df.groupby(filtered_df['date'].dt.to_period('M'))['total'].sum()
                
                fig_pred = go.Figure()
                
                # Historical data
                fig_pred.add_trace(go.Scatter(
                    x=[str(period) for period in monthly_spending.index],
                    y=monthly_spending.values,
                    mode='lines+markers',
                    name='Historical Spending',
                    line=dict(color='blue')
                ))
                
                # Prediction
                next_month = pd.Period.now('M') + 1
                fig_pred.add_trace(go.Scatter(
                    x=[str(next_month)],
                    y=[prediction['predicted_total']],
                    mode='markers',
                    name='Predicted Spending',
                    marker=dict(color='red', size=10)
                ))
                
                fig_pred.update_layout(
                    title='Monthly Spending Prediction',
                    xaxis_title='Month',
                    yaxis_title='Spending ($)'
                )
                
                st.plotly_chart(fig_pred, use_container_width=True)
            
            # Anomaly detection
            st.subheader("Spending Anomalies")
            anomalies = st.session_state.analyzer.detect_spending_anomalies(filtered_receipt_data)
            
            if anomalies:
                st.write(f"Found {len(anomalies)} unusual spending patterns:")
                
                anomaly_df = pd.DataFrame(anomalies)
                anomaly_df['date'] = pd.to_datetime(anomaly_df['date'])
                
                for _, anomaly in anomaly_df.head(10).iterrows():
                    severity = "🔴" if abs(anomaly['z_score']) > 3 else "🟡"
                    st.write(f"{severity} **${anomaly['total']:.2f}** at {anomaly['store_name']} on {anomaly['date'].strftime('%Y-%m-%d')} (Z-score: {anomaly['z_score']:.2f})")
            else:
                st.info("No spending anomalies detected in the selected period.")
        
        with tab4:
            st.header("Spending Insights")
            
            # Generate insights
            insights = st.session_state.analyzer.generate_spending_insights(filtered_receipt_data)
            
            st.subheader("Key Insights")
            for i, insight in enumerate(insights, 1):
                st.info(f"**Insight {i}:** {insight}")
            
            # Savings opportunities
            st.subheader("Savings Opportunities")
            savings_ops = st.session_state.analyzer.calculate_savings_opportunities(filtered_receipt_data)
            
            if savings_ops:
                for category, opportunity in savings_ops.items():
                    with st.expander(f"💰 {category} - Potential Annual Savings: ${opportunity['potential_annual_savings']:.2f}"):
                        st.write(f"**Current Monthly Spending:** ${opportunity['monthly_spending']:.2f}")
                        st.write(f"**Monthly Increase Trend:** ${opportunity['increasing_trend']:.2f}")
                        st.write(f"**Recommendation:** {opportunity['recommendation']}")
            else:
                st.info("No specific savings opportunities identified. Keep tracking your spending!")
            
            # Spending goals
            st.subheader("Set Spending Goals")
            
            col1, col2 = st.columns(2)
            
            with col1:
                monthly_goal = st.number_input(
                    "Monthly Spending Goal ($)",
                    min_value=0.0,
                    value=float(filtered_df['total'].sum() / max(1, len(filtered_df.groupby(filtered_df['date'].dt.to_period('M'))))),
                    step=50.0
                )
            
            with col2:
                current_month_spending = filtered_df[
                    filtered_df['date'].dt.to_period('M') == pd.Period.now('M')
                ]['total'].sum()
                
                progress = min(current_month_spending / monthly_goal, 1.0) if monthly_goal > 0 else 0
                
                st.metric(
                    "This Month's Progress",
                    f"${current_month_spending:.2f}",
                    f"{progress:.1%} of goal"
                )
                
                # Progress bar
                st.progress(progress)
                
                if progress > 1.0:
                    st.warning("⚠️ You've exceeded your monthly goal!")
                elif progress > 0.8:
                    st.warning("⚠️ You're approaching your monthly limit!")
                else:
                    st.success("✅ You're on track with your spending goal!")
    
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

if __name__ == "__main__":
    main()
