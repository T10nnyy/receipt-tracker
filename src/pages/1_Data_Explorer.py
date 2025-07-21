"""
Data Explorer page for receipt management.
Provides search, filtering, editing, and bulk operations.
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from typing import List

from ..core.database import ReceiptDatabase, DatabaseError
from ..core.parsing import TextExtractor
from ..core.algorithms import ReceiptAnalyzer
from ..core.models import Receipt, SearchFilters
from ..ui.components import UIComponents

# Page configuration
st.set_page_config(
    page_title="Data Explorer - Receipt Processor",
    page_icon="🔍",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state for data explorer."""
    if 'db' not in st.session_state:
        st.session_state.db = ReceiptDatabase()
    
    if 'text_extractor' not in st.session_state:
        st.session_state.text_extractor = TextExtractor()
    
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ReceiptAnalyzer()
    
    if 'selected_receipts' not in st.session_state:
        st.session_state.selected_receipts = []


def main():
    """Main data explorer function."""
    initialize_session_state()
    
    st.title("🔍 Data Explorer")
    st.markdown("Search, filter, edit, and manage your receipts")
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Upload & Process", "🔍 Search & Filter", "✏️ Edit Receipts", "📤 Export Data"])
    
    with tab1:
        render_upload_section()
    
    with tab2:
        render_search_section()
    
    with tab3:
        render_edit_section()
    
    with tab4:
        render_export_section()


def render_upload_section():
    """Render file upload and processing section."""
    st.header("📁 Upload New Receipt")
    
    # File upload
    uploaded_file_bytes = UIComponents.render_file_uploader()
    
    if uploaded_file_bytes:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Process Receipt", type="primary", use_container_width=True):
                process_uploaded_file(uploaded_file_bytes)
        
        with col2:
            st.info(f"File ready for processing")
    
    # Batch upload section
    st.markdown("---")
    st.subheader("📚 Batch Upload")
    st.info("💡 **Coming Soon:** Batch processing for multiple receipts")
    
    # Processing history
    st.markdown("---")
    st.subheader("📋 Recent Uploads")
    
    try:
        recent_receipts = st.session_state.db.get_all_receipts(limit=10)
        if recent_receipts:
            # Show recent receipts with processing info
            for receipt in recent_receipts:
                with st.expander(f"📄 {receipt.vendor} - ${receipt.amount} ({receipt.transaction_date})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {receipt.id}")
                        st.write(f"**Vendor:** {receipt.vendor}")
                        st.write(f"**Amount:** ${receipt.amount}")
                        st.write(f"**Date:** {receipt.transaction_date}")
                        st.write(f"**Category:** {receipt.category}")
                    
                    with col2:
                        st.write(f"**Source:** {receipt.source_file}")
                        st.write(f"**Confidence:** {receipt.confidence_score:.1f}%")
                        st.write(f"**Created:** {receipt.created_at}")
                        
                        if st.button(f"🗑️ Delete", key=f"delete_{receipt.id}"):
                            if st.session_state.db.delete_receipt(receipt.id):
                                st.success("Receipt deleted successfully!")
                                st.rerun()
        else:
            st.info("No receipts uploaded yet. Upload your first receipt above!")
            
    except Exception as e:
        st.error(f"Error loading recent receipts: {e}")


def process_uploaded_file(file_bytes: bytes):
    """Process uploaded file and save to database."""
    with st.spinner("🔄 Processing receipt..."):
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name
            
            # Process the file
            result = st.session_state.text_extractor.process_file(
                tmp_file_path,
                f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Clean up
            os.unlink(tmp_file_path)
            
            # Display results
            UIComponents.render_processing_status(result)
            
            if result.success and result.receipt:
                # Show extracted data for review
                st.subheader("📋 Review Extracted Data")
                
                with st.form("review_receipt"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        vendor = st.text_input("Vendor", value=result.receipt.vendor)
                        amount = st.number_input(
                            "Amount ($)",
                            value=float(result.receipt.amount),
                            min_value=0.01,
                            step=0.01,
                            format="%.2f"
                        )
                        transaction_date = st.date_input(
                            "Transaction Date",
                            value=result.receipt.transaction_date
                        )
                    
                    with col2:
                        category = st.selectbox(
                            "Category",
                            options=list(result.receipt.category.__class__),
                            index=list(result.receipt.category.__class__).index(result.receipt.category)
                        )
                        currency = st.selectbox(
                            "Currency",
                            options=list(result.receipt.currency.__class__),
                            index=list(result.receipt.currency.__class__).index(result.receipt.currency)
                        )
                    
                    # Show extracted text
                    if result.receipt.extracted_text:
                        with st.expander("📄 View Extracted Text"):
                            st.text_area(
                                "Raw Text",
                                value=result.receipt.extracted_text,
                                height=200,
                                disabled=True
                            )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        save_button = st.form_submit_button("💾 Save Receipt", type="primary")
                    with col2:
                        discard_button = st.form_submit_button("🗑️ Discard", type="secondary")
                    
                    if save_button:
                        # Update receipt with reviewed data
                        result.receipt.vendor = vendor
                        result.receipt.amount = amount
                        result.receipt.transaction_date = transaction_date
                        result.receipt.category = category
                        result.receipt.currency = currency
                        
                        # Save to database
                        receipt_id = st.session_state.db.add_receipt(result.receipt)
                        st.success(f"✅ Receipt saved successfully with ID: {receipt_id}")
                        st.rerun()
                    
                    if discard_button:
                        st.info("Receipt discarded.")
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ Processing failed: {e}")


def render_search_section():
    """Render search and filtering interface."""
    st.header("🔍 Search & Filter Receipts")
    
    # Search filters
    filters = UIComponents.render_receipt_filters()
    
    # Advanced search options
    with st.expander("🔧 Advanced Search Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            fuzzy_search = st.checkbox("Enable Fuzzy Search", help="Find similar vendor names")
            search_extracted_text = st.checkbox("Search in Extracted Text", help="Search within receipt text content")
        
        with col2:
            confidence_threshold = st.slider(
                "Minimum Confidence Score",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                help="Filter by OCR confidence score"
            )
    
    # Perform search
    try:
        if st.button("🔍 Search Receipts", type="primary"):
            with st.spinner("Searching receipts..."):
                # Get all receipts first
                all_receipts = st.session_state.db.get_all_receipts()
                
                # Apply database-level filters
                filtered_receipts = st.session_state.db.search_receipts(filters)
                
                # Apply additional filters
                if confidence_threshold > 0:
                    filtered_receipts = [
                        r for r in filtered_receipts
                        if (r.confidence_score or 0) >= confidence_threshold
                    ]
                
                # Apply fuzzy search if enabled
                if fuzzy_search and filters.vendor_query:
                    filtered_receipts = st.session_state.analyzer.fuzzy_search_vendors(
                        filtered_receipts,
                        filters.vendor_query,
                        threshold=0.6
                    )
                
                # Apply text search if enabled
                if search_extracted_text and filters.vendor_query:
                    query_lower = filters.vendor_query.lower()
                    filtered_receipts = [
                        r for r in filtered_receipts
                        if query_lower in (r.extracted_text or "").lower()
                    ]
                
                # Store results in session state
                st.session_state.search_results = filtered_receipts
                
                st.success(f"Found {len(filtered_receipts)} matching receipts")
        
        # Display search results
        if hasattr(st.session_state, 'search_results'):
            receipts = st.session_state.search_results
            
            if receipts:
                st.markdown(f"### 📋 Search Results ({len(receipts)} receipts)")
                
                # Sorting options
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    sort_by = st.selectbox(
                        "Sort by",
                        options=['date', 'amount', 'vendor', 'category', 'created'],
                        format_func=lambda x: x.title()
                    )
                
                with col2:
                    sort_ascending = st.checkbox("Ascending", value=False)
                
                with col3:
                    if st.button("🔄 Apply Sort"):
                        sorted_receipts = st.session_state.analyzer.sort_receipts(
                            receipts, sort_by, sort_ascending
                        )
                        st.session_state.search_results = sorted_receipts
                        st.rerun()
                
                # Display results table
                UIComponents.render_receipt_table(receipts, editable=False)
                
                # Bulk operations
                st.markdown("---")
                st.subheader("🔧 Bulk Operations")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📤 Export Results"):
                        UIComponents.render_export_options(receipts)
                
                with col2:
                    if st.button("🗑️ Delete Selected"):
                        st.warning("⚠️ Bulk delete functionality coming soon!")
                
                with col3:
                    if st.button("🏷️ Bulk Categorize"):
                        st.info("💡 Bulk categorization coming soon!")
            
            else:
                st.info("No receipts match your search criteria. Try adjusting your filters.")
        
        else:
            # Show all receipts by default
            all_receipts = st.session_state.db.get_all_receipts(limit=50)
            if all_receipts:
                st.markdown("### 📋 All Receipts (Latest 50)")
                UIComponents.render_receipt_table(all_receipts, editable=False)
            else:
                st.info("No receipts found. Upload some receipts to get started!")
    
    except Exception as e:
        st.error(f"Search failed: {e}")


def render_edit_section():
    """Render receipt editing interface."""
    st.header("✏️ Edit Receipts")
    
    try:
        # Get all receipts for editing
        all_receipts = st.session_state.db.get_all_receipts()
        
        if not all_receipts:
            st.info("No receipts available for editing. Upload some receipts first!")
            return
        
        # Receipt selection
        st.subheader("📋 Select Receipt to Edit")
        
        # Create a more user-friendly selection
        receipt_options = {
            f"ID {r.id}: {r.vendor} - ${r.amount} ({r.transaction_date})": r
            for r in all_receipts
        }
        
        selected_option = st.selectbox(
            "Choose a receipt",
            options=list(receipt_options.keys()),
            help="Select a receipt to edit its details"
        )
        
        if selected_option:
            selected_receipt = receipt_options[selected_option]
            
            # Display current receipt info
            st.markdown("---")
            st.subheader(f"📝 Editing Receipt ID: {selected_receipt.id}")
            
            # Edit form
            with st.form(f"edit_receipt_{selected_receipt.id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    vendor = st.text_input("Vendor", value=selected_receipt.vendor)
                    amount = st.number_input(
                        "Amount ($)",
                        value=float(selected_receipt.amount),
                        min_value=0.01,
                        step=0.01,
                        format="%.2f"
                    )
                    transaction_date = st.date_input(
                        "Transaction Date",
                        value=selected_receipt.transaction_date
                    )
                
                with col2:
                    from ..core.models import CategoryEnum, CurrencyEnum
                    
                    category = st.selectbox(
                        "Category",
                        options=list(CategoryEnum),
                        index=list(CategoryEnum).index(selected_receipt.category)
                    )
                    currency = st.selectbox(
                        "Currency",
                        options=list(CurrencyEnum),
                        index=list(CurrencyEnum).index(selected_receipt.currency)
                    )
                
                # Show extracted text for reference
                if selected_receipt.extracted_text:
                    with st.expander("📄 View Original Extracted Text"):
                        st.text_area(
                            "Raw Text",
                            value=selected_receipt.extracted_text,
                            height=200,
                            disabled=True
                        )
                
                # Form buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    save_button = st.form_submit_button("💾 Save Changes", type="primary")
                
                with col2:
                    reset_button = st.form_submit_button("🔄 Reset", type="secondary")
                
                with col3:
                    delete_button = st.form_submit_button("🗑️ Delete Receipt", type="secondary")
                
                if save_button:
                    # Create updated receipt
                    from decimal import Decimal
                    
                    updated_receipt = Receipt(
                        id=selected_receipt.id,
                        vendor=vendor,
                        transaction_date=transaction_date,
                        amount=Decimal(str(amount)),
                        category=category,
                        currency=currency,
                        source_file=selected_receipt.source_file,
                        extracted_text=selected_receipt.extracted_text,
                        confidence_score=selected_receipt.confidence_score,
                        created_at=selected_receipt.created_at,
                        updated_at=datetime.now()
                    )
                    
                    # Update in database
                    if st.session_state.db.update_receipt(updated_receipt):
                        st.success("✅ Receipt updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update receipt")
                
                if reset_button:
                    st.info("🔄 Form reset. Please refresh to see original values.")
                    st.rerun()
                
                if delete_button:
                    if st.session_state.db.delete_receipt(selected_receipt.id):
                        st.success("🗑️ Receipt deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete receipt")
    
    except Exception as e:
        st.error(f"Error in edit section: {e}")


def render_export_section():
    """Render data export interface."""
    st.header("📤 Export Data")
    
    try:
        # Get receipts for export
        all_receipts = st.session_state.db.get_all_receipts()
        
        if not all_receipts:
            st.info("No receipts available for export.")
            return
        
        st.markdown(f"**Total receipts available:** {len(all_receipts)}")
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Formats")
            
            # CSV Export
            if st.button("📄 Export as CSV", type="primary", use_container_width=True):
                csv_data = UIComponents._generate_csv(all_receipts)
                st.download_button(
                    label="⬇️ Download CSV File",
                    data=csv_data,
                    file_name=f"receipts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # JSON Export
            if st.button("📋 Export as JSON", type="secondary", use_container_width=True):
                json_data = UIComponents._generate_json(all_receipts)
                st.download_button(
                    label="⬇️ Download JSON File",
                    data=json_data,
                    file_name=f"receipts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            st.subheader("🔧 Export Options")
            
            # Filter options for export
            export_filters = UIComponents.render_receipt_filters()
            
            if st.button("🔍 Apply Filters & Export"):
                filtered_receipts = st.session_state.db.search_receipts(export_filters)
                st.session_state.export_receipts = filtered_receipts
                st.success(f"Filtered to {len(filtered_receipts)} receipts for export")
        
        # Preview export data
        st.markdown("---")
        st.subheader("👀 Export Preview")
        
        export_receipts = getattr(st.session_state, 'export_receipts', all_receipts[:10])
        
        if export_receipts:
            # Show preview table
            preview_df = pd.DataFrame([
                {
                    'ID': r.id,
                    'Vendor': r.vendor,
                    'Date': r.transaction_date,
                    'Amount': f"${r.amount:.2f}",
                    'Category': r.category
                }
                for r in export_receipts[:10]
            ])
            
            st.dataframe(preview_df, use_container_width=True)
            
            if len(export_receipts) > 10:
                st.info(f"Showing first 10 of {len(export_receipts)} receipts")
        
        # Export statistics
        st.markdown("---")
        st.subheader("📊 Export Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Receipts", len(all_receipts))
        
        with col2:
            total_amount = sum(float(r.amount) for r in all_receipts)
            st.metric("Total Value", f"${total_amount:,.2f}")
        
        with col3:
            avg_amount = total_amount / len(all_receipts) if all_receipts else 0
            st.metric("Average Amount", f"${avg_amount:.2f}")
    
    except Exception as e:
        st.error(f"Export error: {e}")


if __name__ == "__main__":
    main()
