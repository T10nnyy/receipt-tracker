"""
UI Components Module - Reusable Streamlit Components

This module provides reusable UI components and styling functions for consistent
appearance across the application. Includes custom CSS, navigation elements,
and common interface patterns.

Author: Receipt Processing Team
Version: 1.0.1 - Fixed import handling
"""

import streamlit as st
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import pandas as pd

# Handle imports with fallbacks
try:
    from core.database import DatabaseManager
except ImportError:
    st.warning("Database module not available. Some features may be limited.")
    DatabaseManager = None

try:
    from core.parsing import TextExtractor
except ImportError:
    st.warning("Text extraction module not available. Upload processing disabled.")
    TextExtractor = None

try:
    from core.models import Receipt
except ImportError:
    st.warning("Receipt models not available. Using fallback structure.")
    # Create a simple Receipt class as fallback
    class Receipt:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', '')
            self.store_name = kwargs.get('store_name', 'Unknown')
            self.vendor = kwargs.get('vendor', self.store_name)
            self.total = kwargs.get('total', 0.0)
            self.amount = kwargs.get('amount', self.total)
            self.total_amount = kwargs.get('total_amount', self.amount)
            self.date = kwargs.get('date', datetime.now())
            self.transaction_date = kwargs.get('transaction_date', self.date)
            self.category = kwargs.get('category', 'Other')
            self.payment_method = kwargs.get('payment_method', 'Unknown')
            self.items = kwargs.get('items', [])
            self.created_at = kwargs.get('created_at', datetime.now())
            self.confidence_score = kwargs.get('confidence_score', 0.0)
            self.merchant_name = kwargs.get('merchant_name', self.store_name)

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    st.warning("Plotly not available. Charts will be disabled.")
    PLOTLY_AVAILABLE = False
    px = None
    go = None

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
    
    /* Warning boxes */
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #ffc107;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #17a2b8;
    }
    </style>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create the application sidebar with error handling"""
    with st.sidebar:
        st.header("🧾 Receipt Processor")
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        try:
            # Check if we're in a multi-page app structure
            if os.path.exists("src/pages"):
                st.page_link("src/app.py", label="🏠 Home", icon="🏠")
                st.page_link("src/pages/1_Data_Explorer.py", label="📊 Data Explorer", icon="📊")
                st.page_link("src/pages/2_Analytics_Dashboard.py", label="📈 Analytics", icon="📈")
            else:
                # Fallback navigation
                st.markdown("- 🏠 Home (current)")
                st.markdown("- 📊 Data Explorer")
                st.markdown("- 📈 Analytics")
        except Exception as e:
            st.markdown("Navigation unavailable")
        
        st.markdown("---")
        
        # Quick stats with error handling
        st.subheader("Quick Stats")
        try:
            if DatabaseManager and 'db' in st.session_state and st.session_state.db:
                stats = st.session_state.db.get_statistics()
                st.metric("Total Receipts", getattr(stats, 'total_receipts', 0))
                st.metric("Total Spent", f"${getattr(stats, 'total_spent', 0):.2f}")
                st.metric("This Month", f"${getattr(stats, 'spending_this_month', 0):.2f}")
            else:
                # Fallback stats
                st.metric("Total Receipts", "0")
                st.metric("Total Spent", "$0.00")
                st.metric("This Month", "$0.00")
                if not DatabaseManager:
                    st.caption("Database not connected")
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")
            # Show fallback stats
            st.metric("Total Receipts", "Error")
            st.metric("Total Spent", "Error")
            st.metric("This Month", "Error")
        
        st.markdown("---")
        
        # Settings
        st.subheader("Settings")
        st.selectbox("Theme", ["Light", "Dark"], disabled=True, help="Coming soon!")
        st.selectbox("Currency", ["USD", "EUR", "GBP"], disabled=True, help="Coming soon!")
        
        # System status
        st.markdown("---")
        st.subheader("System Status")
        st.success("✅ UI Components") if True else st.error("❌ UI Components")
        st.success("✅ Database") if DatabaseManager else st.error("❌ Database")
        st.success("✅ Text Extraction") if TextExtractor else st.error("❌ Text Extraction")
        st.success("✅ Charts") if PLOTLY_AVAILABLE else st.error("❌ Charts")

def safe_get_attribute(obj, attr, default=None):
    """Safely get an attribute from an object"""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default

def display_receipt_card(receipt):
    """Display a receipt card with error handling"""
    try:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                store_name = safe_get_attribute(receipt, 'store_name') or safe_get_attribute(receipt, 'vendor') or 'Unknown Store'
                st.write(f"**{store_name}**")
                
                receipt_date = safe_get_attribute(receipt, 'date') or safe_get_attribute(receipt, 'transaction_date')
                if receipt_date:
                    if hasattr(receipt_date, 'strftime'):
                        st.write(f"{receipt_date.strftime('%Y-%m-%d')}")
                    else:
                        st.write(f"{receipt_date}")
                
                items = safe_get_attribute(receipt, 'items', [])
                if items and len(items) > 0:
                    st.write(f"{len(items)} items")
            
            with col2:
                total = safe_get_attribute(receipt, 'total') or safe_get_attribute(receipt, 'amount') or safe_get_attribute(receipt, 'total_amount') or 0
                st.write(f"**${float(total):.2f}**")
                
                category = safe_get_attribute(receipt, 'category') or 'Other'
                st.write(f"_{category}_")
            
            st.markdown("---")
    
    except Exception as e:
        st.error(f"Error displaying receipt: {str(e)}")
        # Show fallback card
        st.write("**Receipt**")
        st.write("Error loading details")
        st.markdown("---")

def create_metrics_row(stats: Dict[str, Any]):
    """Create a row of metrics with error handling"""
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Receipts",
                stats.get('total_receipts', 0)
            )
        
        with col2:
            st.metric(
                "Total Spent",
                f"${stats.get('total_spent', 0):.2f}"
            )
        
        with col3:
            st.metric(
                "Average Receipt",
                f"${stats.get('average_receipt', 0):.2f}"
            )
        
        with col4:
            st.metric(
                "This Month",
                f"${stats.get('spending_this_month', 0):.2f}"
            )
    
    except Exception as e:
        st.error(f"Error creating metrics: {str(e)}")
        # Show fallback metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Receipts", "Error")
        with col2:
            st.metric("Total Spent", "Error")
        with col3:
            st.metric("Average Receipt", "Error")
        with col4:
            st.metric("This Month", "Error")

def create_spending_chart(data: List[Dict[str, Any]], chart_type: str = "bar"):
    """Create a spending chart with error handling"""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts are not available. Install plotly to enable charts.")
        return
    
    try:
        if not data:
            st.info("No data available for chart")
            return
        
        if chart_type == "bar":
            fig = px.bar(
                data,
                x='category',
                y='total',
                title='Spending by Category'
            )
        elif chart_type == "pie":
            fig = px.pie(
                data,
                values='total',
                names='category',
                title='Spending Distribution'
            )
        else:
            fig = px.line(
                data,
                x='date',
                y='total',
                title='Spending Over Time'
            )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        # Show fallback table
        st.subheader("Data Table (Chart unavailable)")
        df = pd.DataFrame(data)
        st.dataframe(df)

def display_error_message(error: str, details: str = None):
    """Display a formatted error message"""
    st.error(f"❌ **Error:** {error}")
    if details:
        with st.expander("Error Details"):
            st.code(details)

def display_success_message(message: str):
    """Display a success message"""
    st.success(f"✅ {message}")

def display_warning_message(message: str):
    """Display a warning message"""
    st.warning(f"⚠️ {message}")

def display_info_message(message: str):
    """Display an info message"""
    st.info(f"ℹ️ {message}")

def create_upload_area():
    """Create a drag-and-drop upload area"""
    uploaded_file = st.file_uploader(
        "Upload Receipt Image",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Drag and drop or click to upload a receipt image",
        accept_multiple_files=False
    )
    
    return uploaded_file

def create_filter_sidebar(df):
    """Create filter controls in sidebar with error handling"""
    try:
        st.sidebar.header("Filters")
        
        filters = {}
        
        if df is None or df.empty:
            st.sidebar.info("No data available for filtering")
            return filters
        
        # Date range filter
        if 'date' in df.columns:
            try:
                min_date = pd.to_datetime(df['date']).min().date()
                max_date = pd.to_datetime(df['date']).max().date()
                
                filters['date_range'] = st.sidebar.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            except Exception as e:
                st.sidebar.error("Error with date filter")
        
        # Category filter
        if 'category' in df.columns:
            try:
                categories = ['All'] + list(df['category'].dropna().unique())
                filters['category'] = st.sidebar.selectbox("Category", categories)
            except Exception:
                st.sidebar.error("Error with category filter")
        
        # Store filter
        if 'store_name' in df.columns:
            try:
                stores = ['All'] + list(df['store_name'].dropna().unique())
                filters['store'] = st.sidebar.selectbox("Store", stores)
            except Exception:
                st.sidebar.error("Error with store filter")
        
        # Amount range filter
        if 'total' in df.columns:
            try:
                min_amount = float(df['total'].min())
                max_amount = float(df['total'].max())
                filters['amount_range'] = st.sidebar.slider(
                    "Amount Range",
                    min_value=min_amount,
                    max_value=max_amount,
                    value=(min_amount, max_amount)
                )
            except Exception:
                st.sidebar.error("Error with amount filter")
        
        return filters
    
    except Exception as e:
        st.sidebar.error(f"Error creating filters: {str(e)}")
        return {}

def apply_filters(df, filters):
    """Apply filters to dataframe with error handling"""
    try:
        if df is None or df.empty or not filters:
            return df
        
        filtered_df = df.copy()
        
        # Apply date filter
        if 'date_range' in filters and len(filters['date_range']) == 2:
            try:
                start_date, end_date = filters['date_range']
                df_dates = pd.to_datetime(filtered_df['date']).dt.date
                filtered_df = filtered_df[
                    (df_dates >= start_date) & 
                    (df_dates <= end_date)
                ]
            except Exception:
                pass  # Skip this filter if it fails
        
        # Apply category filter
        if 'category' in filters and filters['category'] != 'All':
            try:
                filtered_df = filtered_df[filtered_df['category'] == filters['category']]
            except Exception:
                pass
        
        # Apply store filter
        if 'store' in filters and filters['store'] != 'All':
            try:
                filtered_df = filtered_df[filtered_df['store_name'] == filters['store']]
            except Exception:
                pass
        
        # Apply amount filter
        if 'amount_range' in filters:
            try:
                min_amount, max_amount = filters['amount_range']
                filtered_df = filtered_df[
                    (filtered_df['total'] >= min_amount) & 
                    (filtered_df['total'] <= max_amount)
                ]
            except Exception:
                pass
        
        return filtered_df
    
    except Exception as e:
        st.error(f"Error applying filters: {str(e)}")
        return df

def create_export_buttons(df, filename_prefix="receipts"):
    """Create export buttons for data with error handling"""
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export CSV"):
                try:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error creating CSV: {str(e)}")
        
        with col2:
            if st.button("📊 Export Excel"):
                try:
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Data', index=False)
                    
                    st.download_button(
                        label="Download Excel",
                        data=output.getvalue(),
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except ImportError:
                    st.error("Excel export requires openpyxl. Please install it.")
                except Exception as e:
                    st.error(f"Error creating Excel: {str(e)}")
    
    except Exception as e:
        st.error(f"Error creating export buttons: {str(e)}")

def process_quick_upload(uploaded_file):
    """Process a single uploaded file quickly with error handling."""
    if not TextExtractor:
        st.error("Text extraction not available. Please check your installation.")
        return
    
    if not DatabaseManager:
        st.error("Database not available. Please check your installation.")
        return
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Process file
        with st.spinner(f"Processing {uploaded_file.name}..."):
            text_extractor = TextExtractor()
            result = text_extractor.process_file(tmp_file_path, uploaded_file.name)
        
        if hasattr(result, 'success') and result.success and hasattr(result, 'receipt'):
            # Save to database
            db_manager = DatabaseManager()
            receipt_id = db_manager.add_receipt(result.receipt)
            
            st.success(f"✅ Receipt processed and saved! (ID: {receipt_id})")
            
            # Show quick summary
            col1, col2, col3 = st.columns(3)
            with col1:
                vendor = safe_get_attribute(result.receipt, 'vendor', 'Unknown')
                st.metric("Vendor", vendor)
            with col2:
                amount = safe_get_attribute(result.receipt, 'amount', 0)
                st.metric("Amount", f"${float(amount):.2f}")
            with col3:
                confidence = safe_get_attribute(result.receipt, 'confidence_score', 0)
                st.metric("Confidence", f"{float(confidence)*100:.1f}%")
            
            st.balloons()
        else:
            error_msg = getattr(result, 'error_message', 'Processing failed')
            st.error(f"❌ Processing failed: {error_msg}")
        
        # Clean up
        os.unlink(tmp_file_path)
        
    except Exception as e:
        st.error(f"Upload processing failed: {str(e)}")
        # Clean up temp file if it exists
        try:
            if 'tmp_file_path' in locals():
                os.unlink(tmp_file_path)
        except:
            pass

# Additional utility functions with error handling

def safe_render_receipt_card(receipt: Receipt, show_edit: bool = False):
    """Safely render a receipt card with comprehensive error handling."""
    try:
        with st.container():
            # Header with vendor and amount
            col1, col2 = st.columns([3, 1])
            
            with col1:
                vendor = safe_get_attribute(receipt, 'vendor') or safe_get_attribute(receipt, 'store_name') or 'Unknown Vendor'
                st.markdown(f"### 🏪 {vendor}")
                
                category = safe_get_attribute(receipt, 'category') or 'Other'
                st.markdown(f"**Category:** {category}")
            
            with col2:
                amount = safe_get_attribute(receipt, 'amount') or safe_get_attribute(receipt, 'total') or safe_get_attribute(receipt, 'total_amount') or 0
                st.markdown(f"### 💰 ${float(amount):.2f}")
                
                payment_method = safe_get_attribute(receipt, 'payment_method') or 'Unknown'
                st.markdown(f"**{payment_method}**")
            
            # Date and details
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_date = safe_get_attribute(receipt, 'transaction_date') or safe_get_attribute(receipt, 'date')
                if transaction_date and hasattr(transaction_date, 'strftime'):
                    st.markdown(f"**📅 Date:** {transaction_date.strftime('%B %d, %Y')}")
                elif transaction_date:
                    st.markdown(f"**📅 Date:** {transaction_date}")
                
                created_at = safe_get_attribute(receipt, 'created_at')
                if created_at and hasattr(created_at, 'strftime'):
                    st.markdown(f"**⏰ Added:** {created_at.strftime('%m/%d/%Y %H:%M')}")
            
            with col2:
                items = safe_get_attribute(receipt, 'items', [])
                if items and len(items) > 0:
                    st.markdown("**🛍️ Items:**")
                    for item in items[:5]:  # Show first 5 items
                        st.markdown(f"• {item}")
                    if len(items) > 5:
                        st.markdown(f"• ... and {len(items) - 5} more items")
                else:
                    st.markdown("**🛍️ Items:** No items listed")
            
            # Receipt ID (small text)
            receipt_id = safe_get_attribute(receipt, 'id', 'N/A')
            st.caption(f"Receipt ID: {receipt_id}")
            
    except Exception as e:
        st.error(f"Error rendering receipt card: {str(e)}")
        # Fallback display
        st.markdown("### Receipt")
        st.markdown("*Error loading receipt details*")

def show_system_status():
    """Show system status information"""
    st.subheader("🔧 System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Core Components:**")
        st.write("✅ UI Components" if True else "❌ UI Components")
        st.write("✅ Database" if DatabaseManager else "❌ Database")
        st.write("✅ Text Extraction" if TextExtractor else "❌ Text Extraction")
        st.write("✅ Charts" if PLOTLY_AVAILABLE else "❌ Charts")
    
    with col2:
        st.write("**Python Packages:**")
        st.write("✅ Streamlit" if True else "❌ Streamlit")
        st.write("✅ Pandas" if True else "❌ Pandas")
        
        try:
            import plotly
            st.write("✅ Plotly")
        except:
            st.write("❌ Plotly")
        
        try:
            import openpyxl
            st.write("✅ OpenPyXL")
        except:
            st.write("❌ OpenPyXL")

def create_diagnostic_info():
    """Create diagnostic information for troubleshooting"""
    with st.expander("🔍 Diagnostic Information"):
        st.write("**System Information:**")
        st.write(f"- Streamlit version: {st.__version__}")
        st.write(f"- Python version: {os.sys.version}")
        st.write(f"- Current working directory: {os.getcwd()}")
        
        st.write("**Available Modules:**")
        modules_status = {
            "DatabaseManager": DatabaseManager is not None,
            "TextExtractor": TextExtractor is not None,
            "Plotly": PLOTLY_AVAILABLE,
            "Pandas": True,
        }
        
        for module, status in modules_status.items():
            status_icon = "✅" if status else "❌"
            st.write(f"- {module}: {status_icon}")
        
        st.write("**Session State Keys:**")
        for key in st.session_state.keys():
            st.write(f"- {key}: {type(st.session_state[key])}")

def initialize_session_state():
    """Initialize session state with safe defaults"""
    if 'receipts' not in st.session_state:
        st.session_state.receipts = []
    
    if 'db' not in st.session_state:
        if DatabaseManager:
            try:
                st.session_state.db = DatabaseManager()
            except Exception as e:
                st.error(f"Failed to initialize database: {str(e)}")
                st.session_state.db = None
        else:
            st.session_state.db = None
    
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []
    
    if 'filter_settings' not in st.session_state:
        st.session_state.filter_settings = {}

# Export the key functions that the main app needs
__all__ = [
    'apply_custom_css',
    'create_sidebar',
    'display_receipt_card',
    'create_metrics_row',
    'create_spending_chart',
    'display_error_message',
    'display_success_message',
    'display_warning_message',
    'display_info_message',
    'create_upload_area',
    'process_quick_upload',
    'safe_render_receipt_card',
    'show_system_status',
    'initialize_session_state',
    'create_diagnostic_info',
    'safe_get_attribute'
]
