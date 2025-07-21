"""
Main Streamlit application entry point.
Implements multi-page architecture with session state management.
"""

import streamlit as st
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.database import ReceiptDatabase, DatabaseError
from core.parsing import TextExtractor
from core.algorithms import ReceiptAnalyzer
from ui.components import UIComponents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Page configuration
st.set_page_config(
    page_title="Receipt Processor",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'db' not in st.session_state:
        try:
            st.session_state.db = ReceiptDatabase()
        except DatabaseError as e:
            st.error(f"Database initialization failed: {e}")
            st.stop()
    
    if 'text_extractor' not in st.session_state:
        st.session_state.text_extractor = TextExtractor()
    
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ReceiptAnalyzer()
    
    if 'processed_receipts' not in st.session_state:
        st.session_state.processed_receipts = []


def main():
    """Main application function."""
    initialize_session_state()
    
    # Render sidebar
    UIComponents.render_sidebar_info()
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🧾 Receipt Processing Application</h1>
        <p>Professional OCR-powered receipt management with advanced analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Welcome section
    st.markdown("## Welcome to Receipt Processor")
    st.markdown("""
    This application provides comprehensive receipt processing capabilities using advanced OCR technology,
    intelligent data extraction, and powerful analytics tools.
    """)
    
    # Feature overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 Smart Processing</h3>
            <p>Advanced OCR with image preprocessing, multi-format support, and intelligent data extraction.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Analytics Dashboard</h3>
            <p>Comprehensive spending analysis, trends visualization, and detailed reporting.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>✏️ Data Management</h3>
            <p>Manual correction tools, search & filtering, and flexible data export options.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick stats
    try:
        total_receipts = st.session_state.db.get_receipt_count()
        if total_receipts > 0:
            analytics = st.session_state.db.get_analytics()
            
            st.markdown("## 📈 Quick Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Receipts", analytics.total_receipts)
            
            with col2:
                st.metric("Total Spent", f"${analytics.total_amount:,.2f}")
            
            with col3:
                st.metric("Average Amount", f"${analytics.average_amount:.2f}")
            
            with col4:
                if analytics.date_range:
                    days = (analytics.date_range[1] - analytics.date_range[0]).days
                    st.metric("Date Range", f"{days} days")
    
    except Exception as e:
        st.warning(f"Could not load statistics: {e}")
    
    # Quick actions
    st.markdown("## 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📁 Upload New Receipt", type="primary"):
            st.switch_page("pages/1_Data_Explorer.py")
    
    with col2:
        if st.button("📊 View Analytics", type="secondary"):
            st.switch_page("pages/2_Analytics_Dashboard.py")
    
    with col3:
        if st.button("🔍 Browse Receipts", type="secondary"):
            st.switch_page("pages/1_Data_Explorer.py")
    
    # File upload section
    st.markdown("## 📁 Upload Receipt")
    
    uploaded_file_bytes = UIComponents.render_file_uploader()
    
    if uploaded_file_bytes and st.button("Process Receipt", type="primary"):
        with st.spinner("Processing receipt..."):
            try:
                # Save uploaded file temporarily
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                    tmp_file.write(uploaded_file_bytes)
                    tmp_file_path = tmp_file.name
                
                # Process the file
                result = st.session_state.text_extractor.process_file(
                    tmp_file_path, 
                    "uploaded_receipt"
                )
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
                # Display results
                UIComponents.render_processing_status(result)
                
                if result.success and result.receipt:
                    # Save to database
                    receipt_id = st.session_state.db.add_receipt(result.receipt)
                    st.success(f"Receipt saved with ID: {receipt_id}")
                    
                    # Refresh session state
                    st.rerun()
                
            except Exception as e:
                st.error(f"Processing failed: {e}")
    
    # Recent receipts preview
    try:
        recent_receipts = st.session_state.db.get_all_receipts(limit=5)
        if recent_receipts:
            st.markdown("## 📋 Recent Receipts")
            UIComponents.render_receipt_table(recent_receipts, editable=False)
    except Exception as e:
        st.warning(f"Could not load recent receipts: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>Receipt Processing Application v1.0</p>
        <p>Built with Streamlit, OpenCV, Tesseract, and PyMuPDF</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
