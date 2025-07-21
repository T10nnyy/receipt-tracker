"""
Main Streamlit application entry point.
Implements multi-page architecture with session state management.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import core modules
from core.database import DatabaseManager
from ui.components import apply_custom_css, create_sidebar, show_upload_interface

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure Streamlit page
st.set_page_config(
    page_title="Receipt Processing Application",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_database():
    """Initialize the database and create tables if they don't exist."""
    try:
        db_manager = DatabaseManager()
        db_manager.initialize_database()
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

def main():
    """Main application entry point."""
    
    # Apply custom CSS styling
    apply_custom_css()
    
    # Initialize database
    if not initialize_database():
        st.stop()
    
    # Create sidebar navigation
    create_sidebar()
    
    # Main content area
    st.title("🧾 Receipt Processing Application")
    st.markdown("---")
    
    # Welcome section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Welcome to the Receipt Processing Application
        
        This professional application helps you:
        - **Extract data** from receipts and bills automatically
        - **Organize** your financial documents with intelligent categorization
        - **Analyze** spending patterns with comprehensive dashboards
        - **Search** and filter your receipts with advanced tools
        - **Export** data for external analysis
        
        **Supported Formats:** PDF, JPG, PNG, TIFF, BMP (up to 10MB)
        """)
        
        # Quick stats
        try:
            db_manager = DatabaseManager()
            total_receipts = len(db_manager.get_all_receipts())
            if total_receipts > 0:
                st.success(f"📊 **{total_receipts}** receipts currently in your database")
            else:
                st.info("🚀 **Get started** by uploading your first receipt!")
        except Exception as e:
            st.warning("Database connection issue. Please refresh the page.")
    
    with col2:
        st.markdown("### 🚀 Quick Actions")
        
        # Navigation buttons
        if st.button("📤 Upload Receipts", use_container_width=True):
            st.switch_page("pages/1_Data_Explorer.py")
        
        if st.button("📊 View Analytics", use_container_width=True):
            st.switch_page("pages/2_Analytics_Dashboard.py")
        
        if st.button("🔍 Search Receipts", use_container_width=True):
            st.switch_page("pages/1_Data_Explorer.py")
    
    # Feature overview
    st.markdown("---")
    st.markdown("### 🎯 Key Features")
    
    feature_cols = st.columns(4)
    
    with feature_cols[0]:
        st.markdown("""
        **🤖 Smart OCR**
        - Advanced text extraction
        - Image preprocessing
        - Multi-format support
        - High accuracy rates
        """)
    
    with feature_cols[1]:
        st.markdown("""
        **📊 Analytics**
        - Spending insights
        - Vendor analysis
        - Trend detection
        - Custom reports
        """)
    
    with feature_cols[2]:
        st.markdown("""
        **🔍 Search & Filter**
        - Fuzzy matching
        - Date ranges
        - Amount filters
        - Category sorting
        """)
    
    with feature_cols[3]:
        st.markdown("""
        **✏️ Manual Editing**
        - Inline corrections
        - Bulk operations
        - Data validation
        - Export options
        """)
    
    # Upload interface
    st.markdown("---")
    st.markdown("### 📤 Quick Upload")
    show_upload_interface()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Built with ❤️ using Python, Streamlit, and modern web technologies</p>
        <p>© 2024 Receipt Processing Application. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
