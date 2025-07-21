import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import ReceiptDatabase
from core.algorithms import ReceiptAnalyzer

# Page configuration
st.set_page_config(
    page_title="Data Explorer - Receipt Processor",
    page_icon="📊",
    layout="wide"
)

# Initialize components
if 'db' not in st.session_state:
    st.session_state.db = ReceiptDatabase()

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = ReceiptAnalyzer()

def main():
    st.title("📊 Receipt Data Explorer")
    st.markdown("Explore and analyze your receipt data in detail")
    
    # Load data
    try:
        receipts = st.session_state.db.get_all_receipts()
        
        if not receipts:
            st.warning("No receipts found. Please upload some receipts first!")
            return
        
        # Convert to DataFrame for easier manipulation
        receipt_data = []
        for receipt in receipts:
            receipt_dict = receipt.to_dict()
            receipt_data.append(receipt_dict)
        
        df = pd.DataFrame(receipt_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Sidebar filters
        st.sidebar.header("Filters")
        
        # Date range filter
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Category filter
        categories = ['All'] + list(df['category'].unique())
        selected_category = st.sidebar.selectbox("Category", categories)
        
        # Store filter
        stores = ['All'] + list(df['store_name'].unique())
        selected_store = st.sidebar.selectbox("Store", stores)
        
        # Amount range filter
        min_amount = float(df['total'].min())
        max_amount = float(df['total'].max())
        amount_range = st.sidebar.slider(
            "Amount Range",
            min_value=min_amount,
            max_value=max_amount,
            value=(min_amount, max_amount),
            step=0.01
        )
        
        # Apply filters
        filtered_df = df.copy()
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'].dt.date >= start_date) & 
                (filtered_df['date'].dt.date <= end_date)
            ]
        
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        
        if selected_store != 'All':
            filtered_df = filtered_df[filtered_df['store_name'] == selected_store]
        
        filtered_df = filtered_df[
            (filtered_df['total'] >= amount_range[0]) & 
            (filtered_df['total'] <= amount_range[1])
        ]
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Receipts", len(filtered_df))
        
        with col2:
            st.metric("Total Spent", f"${filtered_df['total'].sum():.2f}")
        
        with col3:
            st.metric("Average Receipt", f"${filtered_df['total'].mean():.2f}")
        
        with col4:
            st.metric("Date Range", f"{len(filtered_df['date'].dt.date.unique())} days")
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Receipt List", "📈 Analytics", "🔍 Search", "⚙️ Manage"])
        
        with tab1:
            st.header("Receipt List")
            
            # Display options
            col1, col2 = st.columns([3, 1])
            with col2:
                sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Amount (High)", "Amount (Low)"])
            
            # Sort data
            if sort_by == "Date (Newest)":
                display_df = filtered_df.sort_values('date', ascending=False)
            elif sort_by == "Date (Oldest)":
                display_df = filtered_df.sort_values('date', ascending=True)
            elif sort_by == "Amount (High)":
                display_df = filtered_df.sort_values('total', ascending=False)
            else:  # Amount (Low)
                display_df = filtered_df.sort_values('total', ascending=True)
            
            # Display receipts
            for idx, receipt in display_df.iterrows():
                with st.expander(f"{receipt['store_name']} - ${receipt['total']:.2f} ({receipt['date'].strftime('%Y-%m-%d')})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Store:** {receipt['store_name']}")
                        st.write(f"**Date:** {receipt['date'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Total:** ${receipt['total']:.2f}")
                        st.write(f"**Category:** {receipt['category']}")
                    
                    with col2:
                        if receipt['items']:
                            st.write("**Items:**")
                            for item in receipt['items'][:5]:  # Show first 5 items
                                st.write(f"• {item.get('name', 'Unknown')} - ${item.get('price', 0):.2f}")
                            if len(receipt['items']) > 5:
                                st.write(f"... and {len(receipt['items']) - 5} more items")
                    
                    # Action buttons
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button(f"Edit", key=f"edit_{receipt['receipt_id']}"):
                            st.session_state.edit_receipt_id = receipt['receipt_id']
                    with col_b:
                        if st.button(f"Delete", key=f"delete_{receipt['receipt_id']}"):
                            if st.session_state.db.delete_receipt(receipt['receipt_id']):
                                st.success("Receipt deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete receipt")
                    with col_c:
                        st.write("Coming Soon: Bulk delete functionality coming soon!")
        
        with tab2:
            st.header("Analytics Dashboard")
            
            if len(filtered_df) > 0:
                # Spending over time
                st.subheader("Spending Over Time")
                daily_spending = filtered_df.groupby(filtered_df['date'].dt.date)['total'].sum().reset_index()
                fig_time = px.line(daily_spending, x='date', y='total', title='Daily Spending')
                st.plotly_chart(fig_time, use_container_width=True)
                
                # Category breakdown
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Spending by Category")
                    category_spending = filtered_df.groupby('category')['total'].sum().reset_index()
                    fig_cat = px.pie(category_spending, values='total', names='category')
                    st.plotly_chart(fig_cat, use_container_width=True)
                
                with col2:
                    st.subheader("Top Stores")
                    store_spending = filtered_df.groupby('store_name')['total'].sum().sort_values(ascending=False).head(10).reset_index()
                    fig_store = px.bar(store_spending, x='total', y='store_name', orientation='h')
                    st.plotly_chart(fig_store, use_container_width=True)
                
                # Day of week analysis
                st.subheader("Spending by Day of Week")
                filtered_df['day_of_week'] = filtered_df['date'].dt.day_name()
                dow_spending = filtered_df.groupby('day_of_week')['total'].sum().reindex([
                    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
                ]).reset_index()
                fig_dow = px.bar(dow_spending, x='day_of_week', y='total')
                st.plotly_chart(fig_dow, use_container_width=True)
                
                # Advanced analytics
                st.subheader("Advanced Analytics")
                
                # Generate insights
                insights = st.session_state.analyzer.generate_spending_insights(receipt_data)
                for insight in insights:
                    st.info(insight)
                
                # Spending anomalies
                anomalies = st.session_state.analyzer.detect_spending_anomalies(receipt_data)
                if anomalies:
                    st.subheader("Unusual Spending Detected")
                    for anomaly in anomalies[:5]:  # Show top 5 anomalies
                        st.warning(f"Unusual spending: ${anomaly['total']:.2f} at {anomaly['store_name']} on {anomaly['date']}")
            
            else:
                st.info("No data available for the selected filters.")
        
        with tab3:
            st.header("Search Receipts")
            
            search_query = st.text_input("Search receipts by store name or items", placeholder="Enter search term...")
            
            if search_query:
                search_results = st.session_state.db.search_receipts(search_query)
                
                if search_results:
                    st.write(f"Found {len(search_results)} results:")
                    
                    for receipt in search_results:
                        with st.expander(f"{receipt.store_name} - ${receipt.total:.2f} ({receipt.date.strftime('%Y-%m-%d')})"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Store:** {receipt.store_name}")
                                st.write(f"**Date:** {receipt.date.strftime('%Y-%m-%d')}")
                                st.write(f"**Total:** ${receipt.total:.2f}")
                                st.write(f"**Category:** {receipt.category}")
                            
                            with col2:
                                if receipt.items:
                                    st.write("**Items:**")
                                    for item in receipt.items[:5]:
                                        st.write(f"• {item.name} - ${item.price:.2f}")
                                    if len(receipt.items) > 5:
                                        st.write(f"... and {len(receipt.items) - 5} more items")
                else:
                    st.info("No receipts found matching your search.")
        
        with tab4:
            st.header("Manage Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Export Data")
                
                if st.button("Export to CSV"):
                    csv_data = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"receipts_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                if st.button("Export to Excel"):
                    # Create Excel file in memory
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        filtered_df.to_excel(writer, sheet_name='Receipts', index=False)
                    
                    st.download_button(
                        label="Download Excel",
                        data=output.getvalue(),
                        file_name=f"receipts_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with col2:
                st.subheader("Bulk Operations")
                st.info("Coming Soon: Batch processing for multiple receipts")
                st.info("Coming Soon: Bulk categorization coming soon!")
                
                # Database statistics
                st.subheader("Database Info")
                stats = st.session_state.db.get_statistics()
                st.write(f"Total receipts in database: {stats.total_receipts}")
                st.write(f"Total spending tracked: ${stats.total_spent:.2f}")
                st.write(f"Database size: {len(receipt_data)} records")
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

if __name__ == "__main__":
    main()
