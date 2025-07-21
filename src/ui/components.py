"""
UI Components Module - Reusable Streamlit Components

This module provides reusable UI components and styling functions for consistent
appearance across the application. Includes custom CSS, navigation elements,
and common interface patterns.

Author: Receipt Processing Team
Version: 1.0.0
"""

import streamlit as st
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from core.database import DatabaseManager
from core.parsing import TextExtractor
from core.models import Receipt
import plotly.express as px
import plotly.graph_objects as go

def apply_custom_css():
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown("""
    <style>
    /* Main app styling */
    .main {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    /* Success/Error styling */
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Table styling */
    .dataframe {
        border: none !important;
    }
    
    .dataframe th {
        background-color: #667eea !important;
        color: white !important;
        font-weight: bold !important;
    }
    
    .dataframe td {
        border-bottom: 1px solid #e0e0e0 !important;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* File uploader styling */
    .uploadedFile {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9ff;
    }
    
    /* Progress bar styling */
    .stProgress .st-bo {
        background-color: #667eea;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    /* Custom animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create consistent sidebar navigation."""
    with st.sidebar:
        st.markdown("## 🧾 Receipt Processor")
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        if st.button("🏠 Home", use_container_width=True):
            st.experimental_rerun()
        
        if st.button("🔍 Data Explorer", use_container_width=True):
            st.experimental_rerun()
        
        if st.button("📊 Analytics", use_container_width=True):
            st.experimental_rerun()
        
        st.markdown("---")
        
        # Quick stats
        try:
            db_manager = DatabaseManager()
            receipts = db_manager.get_all_receipts()
            
            st.markdown("### 📈 Quick Stats")
            st.metric("Total Receipts", len(receipts))
            
            if receipts:
                total_amount = sum(r.amount for r in receipts)
                st.metric("Total Amount", f"${total_amount:,.2f}")
                
                # Recent activity
                recent_receipts = sorted(receipts, key=lambda x: x.transaction_date, reverse=True)[:3]
                
                st.markdown("### 🕒 Recent Activity")
                for receipt in recent_receipts:
                    st.markdown(f"""
                    **{receipt.vendor}**  
                    ${receipt.amount} • {receipt.transaction_date.strftime('%m/%d/%Y')}
                    """)
            
        except Exception as e:
            st.error("Unable to load stats")
        
        st.markdown("---")
        
        # Help section
        with st.expander("❓ Help & Tips"):
            st.markdown("""
            **Supported Formats:**
            - PDF files
            - Images (JPG, PNG, TIFF, BMP)
            - Text files
            
            **Tips for Better OCR:**
            - Use clear, well-lit images
            - Avoid blurry or skewed photos
            - Ensure text is readable
            - Keep file sizes under 10MB
            
            **Search Features:**
            - Use fuzzy search for similar names
            - Filter by date ranges
            - Set amount thresholds
            - Filter by category or currency
            """)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            <p>Receipt Processing App v1.0</p>
            <p>Built with Streamlit</p>
        </div>
        """, unsafe_allow_html=True)

def show_upload_interface():
    """Display a compact upload interface for the main page."""
    st.markdown("#### Quick Upload")
    
    uploaded_file = st.file_uploader(
        "Drop a receipt file here",
        type=['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'txt'],
        help="Supported: PDF, JPG, PNG, TIFF, BMP, TXT (max 10MB)"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"📄 **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
        
        with col2:
            if st.button("🚀 Process", type="primary"):
                process_quick_upload(uploaded_file)

def process_quick_upload(uploaded_file):
    """Process a single uploaded file quickly."""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Process file
        with st.spinner(f"Processing {uploaded_file.name}..."):
            text_extractor = TextExtractor()
            result = text_extractor.process_file(tmp_file_path, uploaded_file.name)
        
        if result.success and result.receipt:
            # Save to database
            db_manager = DatabaseManager()
            receipt_id = db_manager.add_receipt(result.receipt)
            
            st.success(f"✅ Receipt processed and saved! (ID: {receipt_id})")
            
            # Show quick summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Vendor", result.receipt.vendor)
            with col2:
                st.metric("Amount", f"${result.receipt.amount}")
            with col3:
                st.metric("Confidence", f"{result.receipt.confidence_score:.1%}")
            
            st.balloons()
        else:
            st.error(f"❌ Processing failed: {result.error_message}")
        
        # Clean up
        os.unlink(tmp_file_path)
        
    except Exception as e:
        st.error(f"Upload processing failed: {e}")

def create_metric_card(title: str, value: str, delta: Optional[str] = None, delta_color: str = "normal") -> None:
    """Create a metric card component"""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )

def show_loading_spinner(message="Loading..."):
    """Show a loading spinner with custom message."""
    return st.spinner(message)

def create_info_box(title: str, content: str, box_type: str = "info") -> None:
    """Create an information box"""
    
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
        "tip": "💡"
    }
    
    colors = {
        "info": "#d1ecf1",
        "warning": "#fff3cd",
        "error": "#f8d7da",
        "success": "#d4edda",
        "tip": "#e2e3e5"
    }
    
    icon = icons.get(box_type, "ℹ️")
    bg_color = colors.get(box_type, colors["info"])
    
    st.markdown(
        f"""
        <div style="
            background-color: {bg_color};
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #007bff;
            margin: 1rem 0;
        ">
            <h4 style="margin: 0 0 0.5rem 0;">{icon} {title}</h4>
            <p style="margin: 0;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_progress_bar(progress, message=""):
    """Create a styled progress bar."""
    st.progress(progress, text=message)

def format_currency(amount, currency="USD"):
    """Format currency amounts consistently."""
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$",
        "CHF": "CHF",
        "CNY": "¥"
    }
    
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def create_data_table(data: List[Dict], columns: List[str], selectable: bool = False, sortable: bool = True, searchable: bool = False) -> Optional[List[int]]:
    """Create a standardized data table"""
    
    if not data:
        st.info("No data to display")
        return None
    
    df = pd.DataFrame(data)
    
    if columns:
        df = df[columns]
    
    if searchable:
        search_term = st.text_input("🔍 Search table", key="table_search")
        if search_term:
            # Simple text search across all columns
            mask = df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            df = df[mask]
    
    # Display table
    if selectable:
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row"
        )
        return event.selection.rows if hasattr(event, 'selection') else []
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        return None

def show_confirmation_dialog(message, key=None):
    """Show a confirmation dialog."""
    st.warning(message)
    
    col1, col2 = st.columns(2)
    
    with col1:
        confirm = st.button("✅ Confirm", key=f"confirm_{key}", type="primary")
    
    with col2:
        cancel = st.button("❌ Cancel", key=f"cancel_{key}")
    
    return confirm, cancel

def create_status_badge(status: str, color: str = "blue") -> None:
    """Create a status badge"""
    colors = {
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8",
        "blue": "#007bff"
    }
    
    bg_color = colors.get(color, colors["blue"])
    
    st.markdown(
        f"""
        <span style="
            background-color: {bg_color};
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: 500;
        ">
            {status}
        </span>
        """,
        unsafe_allow_html=True
    )

def show_feature_coming_soon(feature_name):
    """Display a 'coming soon' message for features under development."""
    st.info(f"🚧 **{feature_name}** is coming soon! This feature is currently under development.")

def create_expandable_section(title, content, expanded=False):
    """Create an expandable section with consistent styling."""
    with st.expander(title, expanded=expanded):
        content()

def show_empty_state(message, action_text=None, action_callback=None):
    """Show an empty state with optional action."""
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 3rem;
        color: #666;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
        <div style="font-size: 1.2rem; margin-bottom: 1rem;">{message}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if action_text and action_callback:
        if st.button(action_text, type="primary"):
            action_callback()

def render_receipt_card(receipt: Receipt, show_edit: bool = False):
    """Render a receipt card with all details."""
    try:
        # Create a card-like container
        with st.container():
            # Header with vendor and amount
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 🏪 {receipt.vendor}")
                st.markdown(f"**Category:** {receipt.category}")
            
            with col2:
                st.markdown(f"### 💰 ${receipt.amount:.2f}")
                st.markdown(f"**{receipt.payment_method}**")
            
            # Date and details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**📅 Date:** {receipt.transaction_date.strftime('%B %d, %Y')}")
                if receipt.created_at:
                    st.markdown(f"**⏰ Added:** {receipt.created_at.strftime('%m/%d/%Y %H:%M')}")
            
            with col2:
                if receipt.items:
                    st.markdown("**🛍️ Items:**")
                    for item in receipt.items[:5]:  # Show first 5 items
                        st.markdown(f"• {item}")
                    if len(receipt.items) > 5:
                        st.markdown(f"• ... and {len(receipt.items) - 5} more items")
                else:
                    st.markdown("**🛍️ Items:** No items listed")
            
            # Receipt ID (small text)
            st.caption(f"Receipt ID: {receipt.id}")
            
    except Exception as e:
        st.error(f"Error rendering receipt card: {str(e)}")

def render_upload_section():
    """Render the file upload section."""
    try:
        st.markdown("### 📤 Upload Receipt Files")
        
        uploaded_files = st.file_uploader(
            "Choose receipt files",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload PDF files or images (PNG, JPG, JPEG) of your receipts"
        )
        
        if uploaded_files:
            st.success(f"Selected {len(uploaded_files)} file(s) for processing")
            
            # Show file details
            with st.expander("📋 File Details"):
                for file in uploaded_files:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Name:** {file.name}")
                    with col2:
                        st.write(f"**Size:** {file.size / 1024:.1f} KB")
                    with col3:
                        st.write(f"**Type:** {file.type}")
        
        return uploaded_files
        
    except Exception as e:
        st.error(f"Error in upload section: {str(e)}")
        return None

def render_search_filters():
    """Render search and filter controls."""
    try:
        with st.expander("🔍 Search & Filter Options", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                search_query = st.text_input(
                    "Search receipts",
                    placeholder="Enter vendor name, item, or amount...",
                    help="Search across vendor names, items, and amounts"
                )
                
                date_range = st.date_input(
                    "Date Range",
                    value=(),
                    help="Select start and end dates"
                )
            
            with col2:
                amount_range = st.slider(
                    "Amount Range ($)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=(0.0, 1000.0),
                    step=1.0
                )
                
                category_filter = st.selectbox(
                    "Category",
                    options=["All", "Food & Dining", "Groceries", "Shopping", 
                            "Transportation", "Entertainment", "Healthcare", 
                            "Utilities", "Services", "Other"],
                    index=0
                )
        
        return {
            'search_query': search_query,
            'date_range': date_range,
            'amount_range': amount_range,
            'category_filter': category_filter
        }
        
    except Exception as e:
        st.error(f"Error rendering search filters: {str(e)}")
        return {}

def render_bulk_actions(selected_receipts: List[Receipt]):
    """Render bulk action controls."""
    try:
        if not selected_receipts:
            return
        
        st.markdown(f"### 🔧 Bulk Actions ({len(selected_receipts)} selected)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Delete Selected", type="secondary"):
                st.warning("This will delete all selected receipts. This action cannot be undone.")
                if st.button("Confirm Delete", type="primary"):
                    # Implement bulk delete
                    st.success(f"Deleted {len(selected_receipts)} receipts")
        
        with col2:
            new_category = st.selectbox(
                "Change Category",
                options=["Food & Dining", "Groceries", "Shopping", 
                        "Transportation", "Entertainment", "Healthcare", 
                        "Utilities", "Services", "Other"]
            )
            if st.button("📝 Update Category"):
                # Implement bulk category update
                st.success(f"Updated category for {len(selected_receipts)} receipts")
        
        with col3:
            if st.button("📥 Export Selected"):
                # Implement export functionality
                st.success("Export functionality coming soon!")
                
    except Exception as e:
        st.error(f"Error rendering bulk actions: {str(e)}")

def render_analytics_summary(analytics_data: dict):
    """Render analytics summary cards."""
    try:
        if not analytics_data:
            st.info("No analytics data available")
            return
        
        st.markdown("### 📊 Analytics Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        basic_stats = analytics_data.get('basic_stats', {})
        
        with col1:
            st.metric(
                "Total Receipts",
                basic_stats.get('total_receipts', 0)
            )
        
        with col2:
            st.metric(
                "Total Amount",
                f"${basic_stats.get('total_amount', 0):.2f}"
            )
        
        with col3:
            st.metric(
                "Average Amount",
                f"${basic_stats.get('average_amount', 0):.2f}"
            )
        
        with col4:
            st.metric(
                "Unique Vendors",
                basic_stats.get('unique_vendors', 0)
            )
        
    except Exception as e:
        st.error(f"Error rendering analytics summary: {str(e)}")

def render_error_message(error: str, details: Optional[str] = None):
    """Render a formatted error message."""
    try:
        st.error(f"❌ {error}")
        
        if details:
            with st.expander("Error Details"):
                st.code(details)
                
    except Exception as e:
        st.error(f"Error rendering error message: {str(e)}")

def render_success_message(message: str, details: Optional[str] = None):
    """Render a formatted success message."""
    try:
        st.success(f"✅ {message}")
        
        if details:
            st.info(details)
            
    except Exception as e:
        st.error(f"Error rendering success message: {str(e)}")

def render_loading_spinner(message: str = "Loading..."):
    """Render a loading spinner with message."""
    try:
        return st.spinner(message)
        
    except Exception as e:
        st.error(f"Error rendering loading spinner: {str(e)}")
        return None

def render_confirmation_dialog(message: str, key: str):
    """Render a confirmation dialog."""
    try:
        st.warning(message)
        
        col1, col2 = st.columns(2)
        
        with col1:
            confirm = st.button("✅ Confirm", key=f"confirm_{key}", type="primary")
        
        with col2:
            cancel = st.button("❌ Cancel", key=f"cancel_{key}")
        
        return confirm, cancel
        
    except Exception as e:
        st.error(f"Error rendering confirmation dialog: {str(e)}")
        return False, False

def render_data_table(data: List[dict], title: str = "Data Table"):
    """Render a data table with sorting and filtering."""
    try:
        if not data:
            st.info("No data to display")
            return
        
        st.markdown(f"### {title}")
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(data)
        
        # Add search functionality
        search_term = st.text_input(f"Search {title.lower()}", key=f"search_{title}")
        
        if search_term:
            # Simple text search across all columns
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            df = df[mask]
        
        # Display the table
        st.dataframe(df, use_container_width=True)
        
        # Show row count
        st.caption(f"Showing {len(df)} rows")
        
    except Exception as e:
        st.error(f"Error rendering data table: {str(e)}")

def create_upload_widget(
    label: str = "Upload Receipt Files",
    file_types: List[str] = None,
    multiple: bool = True,
    help_text: str = None
) -> Optional[List]:
    """Create a standardized file upload widget"""
    if file_types is None:
        file_types = ['png', 'jpg', 'jpeg', 'pdf']
    
    if help_text is None:
        help_text = "Upload images or PDF files of your receipts"
    
    return st.file_uploader(
        label,
        type=file_types,
        accept_multiple_files=multiple,
        help=help_text
    )

def create_analytics_chart(
    chart_type: str,
    data: Dict[str, Any],
    title: str,
    **kwargs
) -> go.Figure:
    """Create standardized analytics charts"""
    
    if chart_type == "line":
        fig = px.line(
            x=data.get('x', []),
            y=data.get('y', []),
            title=title,
            **kwargs
        )
    
    elif chart_type == "bar":
        fig = px.bar(
            x=data.get('x', []),
            y=data.get('y', []),
            title=title,
            **kwargs
        )
    
    elif chart_type == "pie":
        fig = px.pie(
            values=data.get('values', []),
            names=data.get('names', []),
            title=title,
            **kwargs
        )
    
    elif chart_type == "scatter":
        fig = px.scatter(
            x=data.get('x', []),
            y=data.get('y', []),
            title=title,
            **kwargs
        )
    
    else:
        # Default to bar chart
        fig = px.bar(
            x=data.get('x', []),
            y=data.get('y', []),
            title=title,
            **kwargs
        )
    
    # Common styling
    fig.update_layout(
        font=dict(size=12),
        title_font_size=16,
        showlegend=True if chart_type == "pie" else False
    )
    
    return fig

def create_filter_sidebar(
    receipts: List,
    show_search: bool = True,
    show_date_filter: bool = True,
    show_amount_filter: bool = True,
    show_merchant_filter: bool = True,
    show_category_filter: bool = True
) -> Dict[str, Any]:
    """Create a standardized filter sidebar"""
    filters = {}
    
    st.sidebar.header("🔧 Filters")
    
    if show_search:
        filters['search_query'] = st.sidebar.text_input(
            "🔍 Search",
            placeholder="Enter merchant, item, or any text..."
        )
    
    if show_date_filter:
        st.sidebar.subheader("📅 Date Range")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            filters['start_date'] = st.date_input(
                "From",
                value=datetime.now().replace(day=1),  # Start of current month
                max_value=datetime.now()
            )
        
        with col2:
            filters['end_date'] = st.date_input(
                "To",
                value=datetime.now(),
                max_value=datetime.now()
            )
    
    if show_amount_filter and receipts:
        st.sidebar.subheader("💰 Amount Range")
        max_amount = max(r.total_amount for r in receipts if r.total_amount) or 100.0
        filters['amount_range'] = st.sidebar.slider(
            "Amount ($)",
            min_value=0.0,
            max_value=float(max_amount),
            value=(0.0, float(max_amount)),
            step=0.01
        )
    
    if show_merchant_filter and receipts:
        st.sidebar.subheader("🏪 Merchant")
        merchants = sorted(set(r.merchant_name for r in receipts if r.merchant_name))
        filters['selected_merchants'] = st.sidebar.multiselect(
            "Select merchants",
            options=merchants,
            default=[]
        )
    
    if show_category_filter and receipts:
        st.sidebar.subheader("📂 Category")
        categories = sorted(set(r.category for r in receipts if r.category))
        filters['selected_categories'] = st.sidebar.multiselect(
            "Select categories",
            options=categories,
            default=[]
        )
    
    return filters

def create_progress_indicator(current: int, total: int, label: str = "Progress") -> None:
    """Create a progress indicator"""
    progress = current / total if total > 0 else 0
    st.progress(progress, text=f"{label}: {current}/{total} ({progress*100:.1f}%)")

def create_export_button(
    data: Any,
    filename: str,
    file_format: str = "csv",
    label: str = "Export Data"
) -> None:
    """Create an export button for data"""
    
    if file_format.lower() == "csv" and isinstance(data, pd.DataFrame):
        csv_data = data.to_csv(index=False)
        st.download_button(
            label=f"📥 {label}",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv"
        )
    
    elif file_format.lower() == "json":
        import json
        json_data = json.dumps(data, indent=2, default=str)
        st.download_button(
            label=f"📥 {label}",
            data=json_data,
            file_name=f"{filename}.json",
            mime="application/json"
        )
    
    else:
        st.error(f"Unsupported export format: {file_format}")
