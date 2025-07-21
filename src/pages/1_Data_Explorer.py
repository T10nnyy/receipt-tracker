"""
Data Explorer Page - Receipt Management Interface

This page provides comprehensive receipt data management capabilities including
upload, search, filter, edit, and export functionality. Features an interactive
table interface with advanced search capabilities and manual data correction tools.

Author: Receipt Processing Team
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
import json

# Import core modules
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from core.database import DatabaseManager
from core.parsing import TextExtractor
from core.algorithms import ReceiptAnalyzer, SearchFilters
from core.models import Receipt, CategoryEnum, CurrencyEnum, ProcessingResult
from ui.components import apply_custom_css, create_sidebar

# Configure page
st.set_page_config(
    page_title="Data Explorer - Receipt Processing",
    page_icon="🔍",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables."""
    if 'selected_receipts' not in st.session_state:
        st.session_state.selected_receipts = []
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'editing_receipt' not in st.session_state:
        st.session_state.editing_receipt = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

def upload_and_process_files():
    """Handle file upload and processing."""
    st.subheader("📤 Upload Receipts")
    
    uploaded_files = st.file_uploader(
        "Choose receipt files",
        type=['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'txt'],
        accept_multiple_files=True,
        help="Supported formats: PDF, JPG, PNG, TIFF, BMP, TXT (max 10MB each)"
    )
    
    if uploaded_files:
        db_manager = DatabaseManager()
        text_extractor = TextExtractor()
        
        # Process each uploaded file
        for uploaded_file in uploaded_files:
            with st.expander(f"Processing: {uploaded_file.name}", expanded=True):
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Show processing status
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        result = text_extractor.process_file(tmp_file_path, uploaded_file.name)
                    
                    if result.success and result.receipt:
                        # Display extracted data for review
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.success("✅ Processing successful!")
                            st.metric("Confidence Score", f"{result.receipt.confidence_score:.1%}")
                            st.metric("Processing Time", f"{result.processing_time:.2f}s")
                        
                        with col2:
                            st.info("📋 Extracted Data")
                            st.write(f"**Vendor:** {result.receipt.vendor}")
                            st.write(f"**Date:** {result.receipt.transaction_date.strftime('%Y-%m-%d')}")
                            st.write(f"**Amount:** {result.receipt.currency.value} {result.receipt.amount}")
                            st.write(f"**Category:** {result.receipt.category.value.title()}")
                        
                        # Allow manual correction before saving
                        if st.button(f"✏️ Edit Before Saving", key=f"edit_{uploaded_file.name}"):
                            st.session_state.editing_receipt = result.receipt
                            st.session_state.edit_mode = True
                            st.rerun()
                        
                        # Save to database
                        if st.button(f"💾 Save Receipt", key=f"save_{uploaded_file.name}", type="primary"):
                            try:
                                receipt_id = db_manager.add_receipt(result.receipt)
                                st.success(f"Receipt saved with ID: {receipt_id}")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Failed to save receipt: {e}")
                    
                    else:
                        st.error(f"❌ Processing failed: {result.error_message}")
                        
                        # Show extracted text for debugging
                        if result.receipt and result.receipt.extracted_text:
                            with st.expander("🔍 View Extracted Text"):
                                st.text_area("Raw Text", result.receipt.extracted_text, height=200)
                
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_file_path)

def show_search_interface():
    """Display advanced search and filter interface."""
    st.subheader("🔍 Search & Filter")
    
    with st.expander("Search Options", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vendor_query = st.text_input("🏪 Vendor Name", placeholder="Enter vendor name...")
            date_from = st.date_input("📅 From Date", value=None)
            amount_min = st.number_input("💰 Min Amount", min_value=0.0, value=0.0, step=0.01)
        
        with col2:
            category_filter = st.selectbox(
                "🏷️ Category",
                options=[None] + [cat.value for cat in CategoryEnum],
                format_func=lambda x: "All Categories" if x is None else x.title()
            )
            date_to = st.date_input("📅 To Date", value=None)
            amount_max = st.number_input("💰 Max Amount", min_value=0.0, value=10000.0, step=0.01)
        
        with col3:
            currency_filter = st.selectbox(
                "💱 Currency",
                options=[None] + [curr.value for curr in CurrencyEnum],
                format_func=lambda x: "All Currencies" if x is None else x
            )
            confidence_threshold = st.slider("🎯 Min Confidence", 0.0, 1.0, 0.0, 0.1)
            fuzzy_search = st.checkbox("🔤 Fuzzy Search", help="Enable similar name matching")
        
        # Search button
        if st.button("🔍 Search", type="primary"):
            perform_search(
                vendor_query, date_from, date_to, amount_min, amount_max,
                category_filter, currency_filter, confidence_threshold, fuzzy_search
            )

def perform_search(vendor_query, date_from, date_to, amount_min, amount_max, 
                  category_filter, currency_filter, confidence_threshold, fuzzy_search):
    """Execute search with given parameters."""
    try:
        db_manager = DatabaseManager()
        analyzer = ReceiptAnalyzer()
        
        # Get all receipts from database
        all_receipts = db_manager.get_all_receipts()
        
        # Create search filters
        filters = SearchFilters(
            vendor_query=vendor_query if vendor_query else None,
            date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
            date_to=datetime.combine(date_to, datetime.max.time()) if date_to else None,
            amount_min=Decimal(str(amount_min)) if amount_min > 0 else None,
            amount_max=Decimal(str(amount_max)) if amount_max < 10000 else None,
            category=CategoryEnum(category_filter) if category_filter else None,
            currency=CurrencyEnum(currency_filter) if currency_filter else None,
            confidence_threshold=confidence_threshold,
            fuzzy_search=fuzzy_search
        )
        
        # Perform search
        search_results = analyzer.search_receipts(all_receipts, filters)
        st.session_state.search_results = search_results
        
        st.success(f"Found {len(search_results)} matching receipts")
        
    except Exception as e:
        st.error(f"Search failed: {e}")

def display_receipts_table():
    """Display interactive receipts table with selection and actions."""
    st.subheader("📋 Receipt Data")
    
    # Get receipts to display
    db_manager = DatabaseManager()
    
    if st.session_state.search_results:
        receipts = st.session_state.search_results
        st.info(f"Showing {len(receipts)} search results")
    else:
        receipts = db_manager.get_all_receipts()
        st.info(f"Showing all {len(receipts)} receipts")
    
    if not receipts:
        st.warning("No receipts found. Upload some receipts to get started!")
        return
    
    # Convert to DataFrame for display
    df_data = []
    for receipt in receipts:
        df_data.append({
            'ID': receipt.id,
            'Vendor': receipt.vendor,
            'Date': receipt.transaction_date.strftime('%Y-%m-%d'),
            'Amount': f"{receipt.currency.value} {receipt.amount}",
            'Category': receipt.category.value.title(),
            'Confidence': f"{receipt.confidence_score:.1%}",
            'File': receipt.source_file
        })
    
    df = pd.DataFrame(df_data)
    
    # Display table with selection
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        selection_mode="multi-index",
        on_select="rerun"
    )
    
    # Handle selection
    if selected_indices and 'selection' in selected_indices:
        selected_rows = selected_indices['selection']['rows']
        st.session_state.selected_receipts = [receipts[i] for i in selected_rows]
    
    # Action buttons
    if st.session_state.selected_receipts:
        st.subheader("🛠️ Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ Edit Selected", disabled=len(st.session_state.selected_receipts) != 1):
                if len(st.session_state.selected_receipts) == 1:
                    st.session_state.editing_receipt = st.session_state.selected_receipts[0]
                    st.session_state.edit_mode = True
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Delete Selected", type="secondary"):
                delete_selected_receipts()
        
        with col3:
            if st.button("📊 Analyze Selected"):
                analyze_selected_receipts()
        
        with col4:
            if st.button("📤 Export Selected"):
                export_selected_receipts()

def show_edit_interface():
    """Display receipt editing interface."""
    if not st.session_state.editing_receipt:
        return
    
    receipt = st.session_state.editing_receipt
    
    st.subheader("✏️ Edit Receipt")
    
    with st.form("edit_receipt_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            vendor = st.text_input("Vendor", value=receipt.vendor)
            transaction_date = st.date_input("Date", value=receipt.transaction_date.date())
            amount = st.number_input("Amount", value=float(receipt.amount), min_value=0.01, step=0.01)
        
        with col2:
            category = st.selectbox(
                "Category",
                options=[cat.value for cat in CategoryEnum],
                index=list(CategoryEnum).index(receipt.category)
            )
            currency = st.selectbox(
                "Currency",
                options=[curr.value for curr in CurrencyEnum],
                index=list(CurrencyEnum).index(receipt.currency)
            )
            confidence = st.slider("Confidence Score", 0.0, 1.0, receipt.confidence_score, 0.01)
        
        # Show original extracted text
        with st.expander("📄 Original Extracted Text"):
            st.text_area("Raw Text", receipt.extracted_text or "No text available", height=200, disabled=True)
        
        # Form buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Save Changes", type="primary"):
                save_edited_receipt(receipt, vendor, transaction_date, amount, category, currency, confidence)
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.edit_mode = False
                st.session_state.editing_receipt = None
                st.rerun()
        
        with col3:
            if st.form_submit_button("🗑️ Delete Receipt", type="secondary"):
                delete_receipt(receipt.id)

def save_edited_receipt(receipt, vendor, transaction_date, amount, category, currency, confidence):
    """Save edited receipt data."""
    try:
        # Update receipt object
        receipt.vendor = vendor
        receipt.transaction_date = datetime.combine(transaction_date, datetime.min.time())
        receipt.amount = Decimal(str(amount))
        receipt.category = CategoryEnum(category)
        receipt.currency = CurrencyEnum(currency)
        receipt.confidence_score = confidence
        
        # Save to database
        db_manager = DatabaseManager()
        success = db_manager.update_receipt(receipt)
        
        if success:
            st.success("Receipt updated successfully!")
            st.session_state.edit_mode = False
            st.session_state.editing_receipt = None
            st.rerun()
        else:
            st.error("Failed to update receipt")
            
    except Exception as e:
        st.error(f"Error updating receipt: {e}")

def delete_selected_receipts():
    """Delete selected receipts with confirmation."""
    if not st.session_state.selected_receipts:
        return
    
    receipt_count = len(st.session_state.selected_receipts)
    
    if st.button(f"⚠️ Confirm Delete {receipt_count} Receipt(s)", type="secondary"):
        try:
            db_manager = DatabaseManager()
            receipt_ids = [r.id for r in st.session_state.selected_receipts]
            deleted_count = db_manager.bulk_delete_receipts(receipt_ids)
            
            st.success(f"Deleted {deleted_count} receipts")
            st.session_state.selected_receipts = []
            st.rerun()
            
        except Exception as e:
            st.error(f"Error deleting receipts: {e}")

def delete_receipt(receipt_id):
    """Delete a single receipt."""
    try:
        db_manager = DatabaseManager()
        success = db_manager.delete_receipt(receipt_id)
        
        if success:
            st.success("Receipt deleted successfully!")
            st.session_state.edit_mode = False
            st.session_state.editing_receipt = None
            st.rerun()
        else:
            st.error("Failed to delete receipt")
            
    except Exception as e:
        st.error(f"Error deleting receipt: {e}")

def analyze_selected_receipts():
    """Analyze selected receipts."""
    if not st.session_state.selected_receipts:
        return
    
    analyzer = ReceiptAnalyzer()
    analytics = analyzer.generate_analytics(st.session_state.selected_receipts)
    
    st.subheader("📊 Analysis Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Receipts", analytics.total_receipts)
    
    with col2:
        st.metric("Total Amount", f"${analytics.total_amount}")
    
    with col3:
        st.metric("Average Amount", f"${analytics.average_amount}")
    
    with col4:
        st.metric("Median Amount", f"${analytics.median_amount}")
    
    # Vendor breakdown
    if analytics.vendor_stats:
        st.subheader("🏪 Top Vendors")
        vendor_data = []
        for vendor, stats in analytics.vendor_stats.items():
            vendor_data.append({
                'Vendor': vendor,
                'Count': stats['count'],
                'Total': f"${stats['total_amount']}"
            })
        
        st.dataframe(pd.DataFrame(vendor_data), use_container_width=True)

def export_selected_receipts():
    """Export selected receipts to CSV or JSON."""
    if not st.session_state.selected_receipts:
        return
    
    st.subheader("📤 Export Data")
    
    export_format = st.selectbox("Export Format", ["CSV", "JSON"])
    
    if st.button("Download Export"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if export_format == "CSV":
                # Create CSV data
                csv_data = []
                for receipt in st.session_state.selected_receipts:
                    csv_data.append({
                        'ID': receipt.id,
                        'Vendor': receipt.vendor,
                        'Date': receipt.transaction_date.strftime('%Y-%m-%d'),
                        'Amount': str(receipt.amount),
                        'Category': receipt.category.value,
                        'Currency': receipt.currency.value,
                        'Source File': receipt.source_file,
                        'Confidence Score': receipt.confidence_score
                    })
                
                df = pd.DataFrame(csv_data)
                csv_string = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_string,
                    file_name=f"receipts_export_{timestamp}.csv",
                    mime="text/csv"
                )
            
            else:  # JSON
                json_data = []
                for receipt in st.session_state.selected_receipts:
                    json_data.append(receipt.to_dict())
                
                json_string = json.dumps(json_data, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_string,
                    file_name=f"receipts_export_{timestamp}.json",
                    mime="application/json"
                )
            
        except Exception as e:
            st.error(f"Export failed: {e}")

def main():
    """Main page function."""
    # Apply styling
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    create_sidebar()
    
    # Page header
    st.title("🔍 Data Explorer")
    st.markdown("Upload, search, edit, and manage your receipt data")
    st.markdown("---")
    
    # Show edit interface if in edit mode
    if st.session_state.edit_mode:
        show_edit_interface()
        st.markdown("---")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "🔍 Search", "📋 Data Table"])
    
    with tab1:
        upload_and_process_files()
    
    with tab2:
        show_search_interface()
    
    with tab3:
        display_receipts_table()

if __name__ == "__main__":
    main()
