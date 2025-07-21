import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sqlite3
import logging
from typing import List, Dict, Any, Optional
import io
import base64

# Import custom modules
from core.database import DatabaseManager
from core.models import Receipt, ReceiptItem
from core.parsing import TextExtractor
from core.algorithms import ReceiptAnalyzer
from ui.components import create_upload_widget, create_receipt_card, create_analytics_chart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Receipt Processor",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'text_extractor' not in st.session_state:
    st.session_state.text_extractor = TextExtractor()
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = ReceiptAnalyzer()

def main():
    """Main application function"""
    st.title("🧾 Receipt Processor")
    st.markdown("Upload and analyze your receipts with AI-powered text extraction")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Upload & Process", "Data Explorer", "Analytics Dashboard"]
        )
        
        st.header("Quick Stats")
        try:
            receipts = st.session_state.db_manager.get_all_receipts()
            total_receipts = len(receipts)
            total_amount = sum(r.total_amount for r in receipts if r.total_amount)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Receipts", total_receipts)
            with col2:
                st.metric("Total Amount", f"${total_amount:.2f}")
                
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            st.error("Error loading statistics")
    
    # Main content based on selected page
    if page == "Upload & Process":
        upload_and_process_page()
    elif page == "Data Explorer":
        data_explorer_page()
    elif page == "Analytics Dashboard":
        analytics_dashboard_page()

def upload_and_process_page():
    """Upload and process receipts page"""
    st.header("Upload & Process Receipts")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose receipt files",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        accept_multiple_files=True,
        help="Upload images or PDF files of your receipts"
    )
    
    if uploaded_files:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing {uploaded_file.name}...")
                
                # Save uploaded file temporarily
                file_path = f"uploads/{uploaded_file.name}"
                Path("uploads").mkdir(exist_ok=True)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Extract text
                extraction_result = st.session_state.text_extractor.extract_from_file(file_path)
                
                if extraction_result['success']:
                    # Create receipt object
                    receipt = Receipt(
                        filename=uploaded_file.name,
                        raw_text=extraction_result['text'],
                        upload_date=datetime.now(),
                        total_amount=extraction_result.get('total_amount', 0.0),
                        merchant_name=extraction_result.get('merchant_name', ''),
                        receipt_date=extraction_result.get('date'),
                        items=extraction_result.get('items', [])
                    )
                    
                    # Save to database
                    receipt_id = st.session_state.db_manager.save_receipt(receipt)
                    
                    st.success(f"✅ Successfully processed {uploaded_file.name}")
                    
                    # Display extracted information
                    with st.expander(f"View details for {uploaded_file.name}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Extracted Information")
                            st.write(f"**Merchant:** {receipt.merchant_name or 'Not detected'}")
                            st.write(f"**Date:** {receipt.receipt_date or 'Not detected'}")
                            st.write(f"**Total:** ${receipt.total_amount:.2f}")
                            
                        with col2:
                            st.subheader("Raw Text")
                            st.text_area("", receipt.raw_text, height=200, disabled=True)
                        
                        if receipt.items:
                            st.subheader("Items")
                            items_df = pd.DataFrame([
                                {
                                    'Item': item.name,
                                    'Quantity': item.quantity,
                                    'Price': f"${item.price:.2f}"
                                }
                                for item in receipt.items
                            ])
                            st.dataframe(items_df, use_container_width=True)
                
                else:
                    st.error(f"❌ Failed to process {uploaded_file.name}: {extraction_result.get('error', 'Unknown error')}")
                
                # Clean up temporary file
                Path(file_path).unlink(missing_ok=True)
                
            except Exception as e:
                logger.error(f"Error processing {uploaded_file.name}: {e}")
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            
            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Processing complete!")
        st.balloons()

def data_explorer_page():
    """Data explorer page"""
    st.header("Data Explorer")
    
    try:
        receipts = st.session_state.db_manager.get_all_receipts()
        
        if not receipts:
            st.info("No receipts found. Upload some receipts first!")
            return
        
        # Search and filter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_query = st.text_input("Search receipts", placeholder="Enter merchant name, item, etc.")
        
        with col2:
            date_range = st.date_input(
                "Date range",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                max_value=datetime.now()
            )
        
        with col3:
            amount_range = st.slider(
                "Amount range",
                min_value=0.0,
                max_value=max(r.total_amount for r in receipts if r.total_amount) or 100.0,
                value=(0.0, max(r.total_amount for r in receipts if r.total_amount) or 100.0)
            )
        
        # Filter receipts
        filtered_receipts = receipts
        
        if search_query:
            filtered_receipts = st.session_state.analyzer.search_receipts(search_query, filtered_receipts)
        
        # Apply date filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_receipts = [
                r for r in filtered_receipts
                if r.receipt_date and start_date <= r.receipt_date.date() <= end_date
            ]
        
        # Apply amount filter
        filtered_receipts = [
            r for r in filtered_receipts
            if amount_range[0] <= (r.total_amount or 0) <= amount_range[1]
        ]
        
        st.write(f"Found {len(filtered_receipts)} receipts")
        
        # Display receipts
        if filtered_receipts:
            # Create DataFrame for display
            receipts_data = []
            for receipt in filtered_receipts:
                receipts_data.append({
                    'ID': receipt.id,
                    'Filename': receipt.filename,
                    'Merchant': receipt.merchant_name or 'Unknown',
                    'Date': receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else 'Unknown',
                    'Amount': f"${receipt.total_amount:.2f}" if receipt.total_amount else '$0.00',
                    'Items': len(receipt.items) if receipt.items else 0
                })
            
            df = pd.DataFrame(receipts_data)
            
            # Display with selection
            selected_indices = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row"
            )
            
            # Bulk actions
            if selected_indices and len(selected_indices.selection.rows) > 0:
                st.subheader("Bulk Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Delete Selected", type="secondary"):
                        st.info("🚧 Bulk delete functionality coming soon!")
                
                with col2:
                    if st.button("Export Selected", type="secondary"):
                        selected_receipts = [filtered_receipts[i] for i in selected_indices.selection.rows]
                        export_data = []
                        for receipt in selected_receipts:
                            export_data.append({
                                'filename': receipt.filename,
                                'merchant': receipt.merchant_name,
                                'date': receipt.receipt_date.isoformat() if receipt.receipt_date else None,
                                'amount': receipt.total_amount,
                                'raw_text': receipt.raw_text
                            })
                        
                        csv = pd.DataFrame(export_data).to_csv(index=False)
                        st.download_button(
                            "Download CSV",
                            csv,
                            "receipts_export.csv",
                            "text/csv"
                        )
                
                with col3:
                    if st.button("Categorize Selected", type="secondary"):
                        st.info("🚧 Bulk categorization coming soon!")
            
            # Receipt details
            if st.checkbox("Show detailed view"):
                for receipt in filtered_receipts[:5]:  # Limit to first 5 for performance
                    with st.expander(f"{receipt.filename} - {receipt.merchant_name or 'Unknown'}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Date:** {receipt.receipt_date or 'Unknown'}")
                            st.write(f"**Amount:** ${receipt.total_amount:.2f}")
                            st.write(f"**Upload Date:** {receipt.upload_date}")
                        
                        with col2:
                            if receipt.items:
                                st.write("**Items:**")
                                for item in receipt.items:
                                    st.write(f"- {item.name}: ${item.price:.2f}")
                        
                        st.text_area("Raw Text", receipt.raw_text, height=100, disabled=True)
        
    except Exception as e:
        logger.error(f"Error in data explorer: {e}")
        st.error(f"Error loading data: {str(e)}")

def analytics_dashboard_page():
    """Analytics dashboard page"""
    st.header("Analytics Dashboard")
    
    try:
        receipts = st.session_state.db_manager.get_all_receipts()
        
        if not receipts:
            st.info("No receipts found. Upload some receipts first!")
            return
        
        # Generate analytics
        analytics = st.session_state.analyzer.generate_analytics(receipts)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Receipts",
                analytics['total_receipts'],
                delta=f"+{analytics.get('receipts_this_month', 0)} this month"
            )
        
        with col2:
            st.metric(
                "Total Spent",
                f"${analytics['total_amount']:.2f}",
                delta=f"${analytics.get('amount_this_month', 0):.2f} this month"
            )
        
        with col3:
            st.metric(
                "Average Receipt",
                f"${analytics['average_amount']:.2f}"
            )
        
        with col4:
            st.metric(
                "Unique Merchants",
                analytics['unique_merchants']
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Spending over time
            if analytics.get('spending_by_date'):
                dates = list(analytics['spending_by_date'].keys())
                amounts = list(analytics['spending_by_date'].values())
                
                fig = px.line(
                    x=dates,
                    y=amounts,
                    title="Spending Over Time",
                    labels={'x': 'Date', 'y': 'Amount ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top merchants
            if analytics.get('top_merchants'):
                merchants = list(analytics['top_merchants'].keys())
                amounts = list(analytics['top_merchants'].values())
                
                fig = px.bar(
                    x=amounts,
                    y=merchants,
                    orientation='h',
                    title="Top Merchants by Spending",
                    labels={'x': 'Amount ($)', 'y': 'Merchant'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Monthly breakdown
        st.subheader("Monthly Breakdown")
        if analytics.get('monthly_breakdown'):
            monthly_df = pd.DataFrame(analytics['monthly_breakdown'])
            st.dataframe(monthly_df, use_container_width=True)
        
        # Patterns and insights
        st.subheader("Insights & Patterns")
        patterns = st.session_state.analyzer.detect_patterns(receipts)
        
        for pattern in patterns:
            st.info(f"💡 {pattern['description']}")
    
    except Exception as e:
        logger.error(f"Error in analytics dashboard: {e}")
        st.error(f"Error generating analytics: {str(e)}")

if __name__ == "__main__":
    main()
