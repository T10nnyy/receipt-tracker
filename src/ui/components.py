"""
Reusable UI components for the Streamlit application.
Provides consistent styling and functionality across pages.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Callable

from ..core.models import Receipt, SearchFilters, CategoryEnum, CurrencyEnum


class UIComponents:
    """Collection of reusable UI components."""
    
    @staticmethod
    def render_receipt_filters() -> SearchFilters:
        """
        Render search and filter controls.
        
        Returns:
            SearchFilters object with user inputs
        """
        st.subheader("🔍 Search & Filter")
        
        col1, col2 = st.columns(2)
        
        with col1:
            vendor_query = st.text_input(
                "Vendor Search",
                placeholder="Search by vendor name...",
                help="Enter partial vendor name to search"
            )
            
            date_from = st.date_input(
                "From Date",
                value=None,
                help="Filter receipts from this date onwards"
            )
            
            amount_min = st.number_input(
                "Minimum Amount ($)",
                min_value=0.01,
                value=None,
                step=0.01,
                format="%.2f",
                help="Filter receipts with amount greater than or equal to this value"
            )
        
        with col2:
            category = st.selectbox(
                "Category",
                options=[None] + list(CategoryEnum),
                format_func=lambda x: "All Categories" if x is None else x,
                help="Filter by receipt category"
            )
            
            date_to = st.date_input(
                "To Date",
                value=None,
                help="Filter receipts up to this date"
            )
            
            amount_max = st.number_input(
                "Maximum Amount ($)",
                min_value=0.01,
                value=None,
                step=0.01,
                format="%.2f",
                help="Filter receipts with amount less than or equal to this value"
            )
        
        currency = st.selectbox(
            "Currency",
            options=[None] + list(CurrencyEnum),
            format_func=lambda x: "All Currencies" if x is None else x,
            help="Filter by currency"
        )
        
        return SearchFilters(
            vendor_query=vendor_query if vendor_query else None,
            date_from=date_from,
            date_to=date_to,
            amount_min=Decimal(str(amount_min)) if amount_min else None,
            amount_max=Decimal(str(amount_max)) if amount_max else None,
            category=category,
            currency=currency
        )
    
    @staticmethod
    def render_receipt_table(receipts: List[Receipt], editable: bool = False) -> Optional[Receipt]:
        """
        Render receipts in a table format with optional editing.
        
        Args:
            receipts: List of receipts to display
            editable: Whether to allow inline editing
            
        Returns:
            Modified receipt if editing occurred, None otherwise
        """
        if not receipts:
            st.info("No receipts found matching your criteria.")
            return None
        
        # Convert receipts to DataFrame for display
        df_data = []
        for receipt in receipts:
            df_data.append({
                'ID': receipt.id,
                'Vendor': receipt.vendor,
                'Date': receipt.transaction_date,
                'Amount': f"${receipt.amount:.2f}",
                'Category': receipt.category,
                'Currency': receipt.currency,
                'Confidence': f"{receipt.confidence_score:.1f}%" if receipt.confidence_score else "N/A"
            })
        
        df = pd.DataFrame(df_data)
        
        if editable:
            st.subheader("📝 Edit Receipts")
            
            # Select receipt to edit
            selected_id = st.selectbox(
                "Select Receipt to Edit",
                options=[r.id for r in receipts],
                format_func=lambda x: f"ID {x}: {next(r.vendor for r in receipts if r.id == x)}"
            )
            
            if selected_id:
                selected_receipt = next(r for r in receipts if r.id == selected_id)
                return UIComponents._render_receipt_editor(selected_receipt)
        else:
            # Display table with sorting options
            sort_options = ['Date', 'Amount', 'Vendor', 'Category']
            sort_by = st.selectbox("Sort by", sort_options, index=0)
            sort_ascending = st.checkbox("Ascending", value=False)
            
            # Sort DataFrame
            sort_column_map = {
                'Date': 'Date',
                'Amount': 'Amount',
                'Vendor': 'Vendor',
                'Category': 'Category'
            }
            
            if sort_by in sort_column_map:
                df = df.sort_values(
                    by=sort_column_map[sort_by],
                    ascending=sort_ascending
                )
            
            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Amount': st.column_config.NumberColumn(
                        'Amount',
                        format="$%.2f"
                    ),
                    'Date': st.column_config.DateColumn(
                        'Date',
                        format="YYYY-MM-DD"
                    )
                }
            )
        
        return None
    
    @staticmethod
    def _render_receipt_editor(receipt: Receipt) -> Optional[Receipt]:
        """
        Render receipt editing form.
        
        Args:
            receipt: Receipt to edit
            
        Returns:
            Modified receipt if changes were made
        """
        with st.form(f"edit_receipt_{receipt.id}"):
            st.write(f"**Editing Receipt ID: {receipt.id}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                vendor = st.text_input("Vendor", value=receipt.vendor)
                transaction_date = st.date_input("Date", value=receipt.transaction_date)
                amount = st.number_input(
                    "Amount",
                    value=float(receipt.amount),
                    min_value=0.01,
                    step=0.01,
                    format="%.2f"
                )
            
            with col2:
                category = st.selectbox(
                    "Category",
                    options=list(CategoryEnum),
                    index=list(CategoryEnum).index(receipt.category)
                )
                currency = st.selectbox(
                    "Currency",
                    options=list(CurrencyEnum),
                    index=list(CurrencyEnum).index(receipt.currency)
                )
            
            # Show extracted text for reference
            if receipt.extracted_text:
                with st.expander("View Extracted Text"):
                    st.text_area(
                        "Raw Text",
                        value=receipt.extracted_text,
                        height=150,
                        disabled=True
                    )
            
            submitted = st.form_submit_button("Save Changes", type="primary")
            
            if submitted:
                # Create updated receipt
                updated_receipt = Receipt(
                    id=receipt.id,
                    vendor=vendor,
                    transaction_date=transaction_date,
                    amount=Decimal(str(amount)),
                    category=category,
                    currency=currency,
                    source_file=receipt.source_file,
                    extracted_text=receipt.extracted_text,
                    confidence_score=receipt.confidence_score,
                    created_at=receipt.created_at,
                    updated_at=datetime.now()
                )
                
                st.success("Receipt updated successfully!")
                return updated_receipt
        
        return None
    
    @staticmethod
    def render_analytics_charts(analytics_data: Dict[str, Any]):
        """
        Render analytics charts and visualizations.
        
        Args:
            analytics_data: Analytics data to visualize
        """
        if not analytics_data:
            st.info("No data available for analytics.")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Receipts",
                analytics_data.get('total_receipts', 0)
            )
        
        with col2:
            total_amount = analytics_data.get('total_amount', 0)
            st.metric(
                "Total Spent",
                f"${total_amount:,.2f}"
            )
        
        with col3:
            avg_amount = analytics_data.get('average_amount', 0)
            st.metric(
                "Average Amount",
                f"${avg_amount:.2f}"
            )
        
        with col4:
            date_range = analytics_data.get('date_range')
            if date_range:
                days = (date_range[1] - date_range[0]).days
                st.metric("Date Range", f"{days} days")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Top vendors chart
            top_vendors = analytics_data.get('top_vendors', [])
            if top_vendors:
                st.subheader("Top Vendors by Spending")
                
                vendors_df = pd.DataFrame(top_vendors)
                fig = px.bar(
                    vendors_df.head(10),
                    x='total_amount',
                    y='vendor',
                    orientation='h',
                    title="Top 10 Vendors",
                    labels={'total_amount': 'Total Amount ($)', 'vendor': 'Vendor'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category breakdown
            category_breakdown = analytics_data.get('category_breakdown', [])
            if category_breakdown:
                st.subheader("Spending by Category")
                
                categories_df = pd.DataFrame(category_breakdown)
                fig = px.pie(
                    categories_df,
                    values='total_amount',
                    names='category',
                    title="Category Distribution"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Monthly trends
        monthly_trends = analytics_data.get('monthly_trends', [])
        if monthly_trends:
            st.subheader("Monthly Spending Trends")
            
            trends_df = pd.DataFrame(monthly_trends)
            trends_df = trends_df.sort_values('month')
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trends_df['month'],
                y=trends_df['total_amount'],
                mode='lines+markers',
                name='Total Amount',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Monthly Spending Trend",
                xaxis_title="Month",
                yaxis_title="Total Amount ($)",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_file_uploader() -> Optional[bytes]:
        """
        Render file upload widget with validation.
        
        Returns:
            Uploaded file bytes or None
        """
        st.subheader("📁 Upload Receipt")
        
        uploaded_file = st.file_uploader(
            "Choose a receipt file",
            type=['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp'],
            help="Supported formats: PDF, JPG, PNG, TIFF, BMP (Max size: 10MB)"
        )
        
        if uploaded_file is not None:
            # Validate file size (10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error("File size exceeds 10MB limit. Please upload a smaller file.")
                return None
            
            # Display file info
            st.info(f"**File:** {uploaded_file.name} ({uploaded_file.size:,} bytes)")
            
            return uploaded_file.getvalue()
        
        return None
    
    @staticmethod
    def render_export_options(receipts: List[Receipt]):
        """
        Render data export options.
        
        Args:
            receipts: List of receipts to export
        """
        if not receipts:
            return
        
        st.subheader("📤 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV Export
            if st.button("Export as CSV", type="secondary"):
                csv_data = UIComponents._generate_csv(receipts)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"receipts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # JSON Export
            if st.button("Export as JSON", type="secondary"):
                json_data = UIComponents._generate_json(receipts)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"receipts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    @staticmethod
    def _generate_csv(receipts: List[Receipt]) -> str:
        """Generate CSV data from receipts."""
        df_data = []
        for receipt in receipts:
            df_data.append({
                'ID': receipt.id,
                'Vendor': receipt.vendor,
                'Date': receipt.transaction_date.isoformat(),
                'Amount': float(receipt.amount),
                'Category': receipt.category,
                'Currency': receipt.currency,
                'Source File': receipt.source_file,
                'Confidence Score': receipt.confidence_score,
                'Created At': receipt.created_at.isoformat() if receipt.created_at else '',
                'Updated At': receipt.updated_at.isoformat() if receipt.updated_at else ''
            })
        
        df = pd.DataFrame(df_data)
        return df.to_csv(index=False)
    
    @staticmethod
    def _generate_json(receipts: List[Receipt]) -> str:
        """Generate JSON data from receipts."""
        import json
        
        json_data = []
        for receipt in receipts:
            json_data.append({
                'id': receipt.id,
                'vendor': receipt.vendor,
                'transaction_date': receipt.transaction_date.isoformat(),
                'amount': float(receipt.amount),
                'category': receipt.category,
                'currency': receipt.currency,
                'source_file': receipt.source_file,
                'extracted_text': receipt.extracted_text,
                'confidence_score': receipt.confidence_score,
                'created_at': receipt.created_at.isoformat() if receipt.created_at else None,
                'updated_at': receipt.updated_at.isoformat() if receipt.updated_at else None
            })
        
        return json.dumps(json_data, indent=2)
    
    @staticmethod
    def render_processing_status(processing_result):
        """
        Render processing status and results.
        
        Args:
            processing_result: ProcessingResult object
        """
        if processing_result.success:
            st.success("✅ File processed successfully!")
            
            if processing_result.processing_time:
                st.info(f"⏱️ Processing time: {processing_result.processing_time:.2f} seconds")
            
            # Show warnings if any
            if processing_result.warnings:
                st.warning("⚠️ **Warnings:**")
                for warning in processing_result.warnings:
                    st.write(f"• {warning}")
            
            # Display extracted data
            if processing_result.receipt:
                receipt = processing_result.receipt
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Extracted Information:**")
                    st.write(f"• **Vendor:** {receipt.vendor}")
                    st.write(f"• **Date:** {receipt.transaction_date}")
                    st.write(f"• **Amount:** ${receipt.amount}")
                    st.write(f"• **Category:** {receipt.category}")
                
                with col2:
                    st.write("**Processing Details:**")
                    st.write(f"• **Currency:** {receipt.currency}")
                    st.write(f"• **Confidence:** {receipt.confidence_score:.1f}%")
                    st.write(f"• **Source:** {receipt.source_file}")
        else:
            st.error(f"❌ Processing failed: {processing_result.error_message}")
    
    @staticmethod
    def render_sidebar_info():
        """Render sidebar information and navigation."""
        with st.sidebar:
            st.title("🧾 Receipt Processor")
            st.markdown("---")
            
            st.markdown("""
            ### Features
            - 📁 Multi-format file support (PDF, Images)
            - 🔍 Advanced OCR text extraction
            - 📊 Comprehensive analytics
            - ✏️ Manual data correction
            - 📤 Data export (CSV, JSON)
            - 🔎 Intelligent search & filtering
            """)
            
            st.markdown("---")
            
            st.markdown("""
            ### Supported Formats
            - **PDF:** Text-based and scanned
            - **Images:** JPG, PNG, TIFF, BMP
            - **Max Size:** 10MB per file
            """)
            
            st.markdown("---")
            
            st.markdown("""
            ### Tips for Better Results
            - Use high-quality, well-lit images
            - Ensure receipts are flat and unfolded
            - Avoid blurry or skewed images
            - Review and correct extracted data
            """)
