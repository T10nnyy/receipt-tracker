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
from PIL import Image
import os
import sys
from streamlit.web import cli as stcli


# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom modules
from core.database import ReceiptDatabase
from core.parsing import ReceiptParser
from core.models import Receipt
from ui.components import create_sidebar, display_receipt_card, create_metrics_row

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
if 'db' not in st.session_state:
    st.session_state.db = ReceiptDatabase()

if 'parser' not in st.session_state:
    st.session_state.parser = ReceiptParser()

def main():
    """Main application function"""
    st.title("🧾 Receipt Processor")
    st.markdown("Upload and analyze your receipts with AI-powered OCR")
    
    # Create sidebar
    create_sidebar()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Upload Receipt")
        uploaded_file = st.file_uploader(
            "Choose a receipt image",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Upload a clear image of your receipt"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Receipt", use_column_width=True)
                
                # Process button
                if st.button("Process Receipt", type="primary"):
                    with st.spinner("Processing receipt..."):
                        try:
                            # Parse the receipt
                            receipt_data = st.session_state.parser.parse_image(image)
                            
                            # Create receipt object
                            receipt = Receipt(
                                store_name=receipt_data.get('store_name', 'Unknown'),
                                date=receipt_data.get('date', datetime.now()),
                                total=receipt_data.get('total', 0.0),
                                items=receipt_data.get('items', []),
                                category=receipt_data.get('category', 'Other')
                            )
                            
                            # Save to database
                            receipt_id = st.session_state.db.add_receipt(receipt)
                            
                            st.success(f"Receipt processed successfully! ID: {receipt_id}")
                            
                            # Display parsed data
                            st.subheader("Parsed Information")
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.write(f"**Store:** {receipt.store_name}")
                                st.write(f"**Date:** {receipt.date.strftime('%Y-%m-%d')}")
                                st.write(f"**Total:** ${receipt.total:.2f}")
                            
                            with col_b:
                                st.write(f"**Category:** {receipt.category}")
                                st.write(f"**Items:** {len(receipt.items)}")
                            
                            # Display items
                            if receipt.items:
                                st.subheader("Items")
                                items_df = pd.DataFrame(receipt.items)
                                st.dataframe(items_df, use_container_width=True)
                                
                        except Exception as e:
                            st.error(f"Error processing receipt: {str(e)}")
    
    with col2:
        st.header("Recent Receipts")
        
        # Get recent receipts
        try:
            recent_receipts = st.session_state.db.get_recent_receipts(limit=5)
            
            if recent_receipts:
                for receipt in recent_receipts:
                    display_receipt_card(receipt)
            else:
                st.info("No receipts found. Upload your first receipt!")
                
        except Exception as e:
            st.error(f"Error loading receipts: {str(e)}")
    
    # Quick stats
    st.header("Quick Statistics")
    try:
        stats = st.session_state.db.get_statistics()
        create_metrics_row(stats)
        
        # Simple chart
        if stats['total_receipts'] > 0:
            # Get spending by category
            category_data = st.session_state.db.get_spending_by_category()
            if category_data:
                df = pd.DataFrame(category_data)
                fig = px.pie(df, values='total', names='category', title='Spending by Category')
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8501))
    sys.argv = ["streamlit", "run", "src/app.py", "--server.port", str(port), "--server.address", "0.0.0.0"]
    sys.exit(stcli.main())
