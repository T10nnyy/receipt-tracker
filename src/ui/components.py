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

# Import core modules
import sys
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from core.database import DatabaseManager
from core.parsing import TextExtractor

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
            st.switch_page("app.py")
        
        if st.button("🔍 Data Explorer", use_container_width=True):
            st.switch_page("pages/1_Data_Explorer.py")
        
        if st.button("📊 Analytics", use_container_width=True):
            st.switch_page("pages/2_Analytics_Dashboard.py")
        
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

def create_metric_card(title, value, delta=None, help_text=None):
    """Create a styled metric card."""
    delta_html = ""
    if delta:
        delta_color = "green" if delta > 0 else "red"
        delta_symbol = "↗" if delta > 0 else "↘"
        delta_html = f"""
        <div style="color: {delta_color}; font-size: 0.8em; margin-top: 0.5rem;">
            {delta_symbol} {delta}
        </div>
        """
    
    help_html = ""
    if help_text:
        help_html = f"""
        <div style="color: #666; font-size: 0.7em; margin-top: 0.5rem;">
            {help_text}
        </div>
        """
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.8em; color: #666; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 2em; font-weight: bold; color: #333;">{value}</div>
        {delta_html}
        {help_html}
    </div>
    """, unsafe_allow_html=True)

def show_loading_spinner(message="Loading..."):
    """Show a loading spinner with custom message."""
    return st.spinner(message)

def create_info_box(message, box_type="info"):
    """Create styled info boxes."""
    colors = {
        "info": {"bg": "#d1ecf1", "border": "#bee5eb", "text": "#0c5460"},
        "success": {"bg": "#d4edda", "border": "#c3e6cb", "text": "#155724"},
        "warning": {"bg": "#fff3cd", "border": "#ffeaa7", "text": "#856404"},
        "error": {"bg": "#f8d7da", "border": "#f5c6cb", "text": "#721c24"}
    }
    
    color = colors.get(box_type, colors["info"])
    
    st.markdown(f"""
    <div style="
        background-color: {color['bg']};
        border: 1px solid {color['border']};
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: {color['text']};
    ">
        {message}
    </div>
    """, unsafe_allow_html=True)

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

def create_data_table(data, columns=None, key=None):
    """Create a styled data table with consistent formatting."""
    if columns:
        data = data[columns]
    
    return st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        key=key
    )

def show_confirmation_dialog(message, key=None):
    """Show a confirmation dialog."""
    st.warning(message)
    
    col1, col2 = st.columns(2)
    
    with col1:
        confirm = st.button("✅ Confirm", key=f"confirm_{key}", type="primary")
    
    with col2:
        cancel = st.button("❌ Cancel", key=f"cancel_{key}")
    
    return confirm, cancel

def create_status_badge(status, text):
    """Create a status badge with appropriate styling."""
    colors = {
        "success": {"bg": "#28a745", "text": "white"},
        "warning": {"bg": "#ffc107", "text": "black"},
        "error": {"bg": "#dc3545", "text": "white"},
        "info": {"bg": "#17a2b8", "text": "white"},
        "secondary": {"bg": "#6c757d", "text": "white"}
    }
    
    color = colors.get(status, colors["secondary"])
    
    return f"""
    <span style="
        background-color: {color['bg']};
        color: {color['text']};
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
    ">
        {text}
    </span>
    """

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
