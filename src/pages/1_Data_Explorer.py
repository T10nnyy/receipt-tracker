import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import logging

from core.database import DatabaseManager
from core.algorithms import ReceiptAnalyzer

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Data Explorer - Receipt Processor",
    page_icon="🔍",
    layout="wide"
)

# Initialize components
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = ReceiptAnalyzer()

def main():
    st.title("🔍 Data Explorer")
    st.markdown("Search, filter, and explore your receipt data")
    
    try:
        receipts = st.session_state.db_manager.get_all_receipts()
        
        if not receipts:
            st.info("📝 No receipts found. Upload some receipts first!")
            if st.button("Go to Upload Page"):
                st.switch_page("src/app.py")
            return
        
        # Sidebar filters
        with st.sidebar:
            st.header("🔧 Filters")
            
            # Search
            search_query = st.text_input(
                "🔍 Search",
                placeholder="Enter merchant, item, or any text...",
                help="Search across all receipt data"
            )
            
            # Date range filter
            st.subheader("📅 Date Range")
            date_col1, date_col2 = st.columns(2)
            
            with date_col1:
                start_date = st.date_input(
                    "From",
                    value=datetime.now() - timedelta(days=90),
                    max_value=datetime.now()
                )
            
            with date_col2:
                end_date = st.date_input(
                    "To",
                    value=datetime.now(),
                    max_value=datetime.now()
                )
            
            # Amount range filter
            st.subheader("💰 Amount Range")
            max_amount = max(r.total_amount for r in receipts if r.total_amount) or 100.0
            amount_range = st.slider(
                "Amount ($)",
                min_value=0.0,
                max_value=float(max_amount),
                value=(0.0, float(max_amount)),
                step=0.01
            )
            
            # Merchant filter
            st.subheader("🏪 Merchant")
            merchants = sorted(set(r.merchant_name for r in receipts if r.merchant_name))
            selected_merchants = st.multiselect(
                "Select merchants",
                options=merchants,
                default=[]
            )
            
            # Category filter
            st.subheader("📂 Category")
            categories = sorted(set(r.category for r in receipts if r.category))
            selected_categories = st.multiselect(
                "Select categories",
                options=categories,
                default=[]
            )
        
        # Apply filters
        filtered_receipts = receipts.copy()
        
        # Search filter
        if search_query:
            filtered_receipts = st.session_state.analyzer.search_receipts(search_query, filtered_receipts)
        
        # Date filter
        filtered_receipts = [
            r for r in filtered_receipts
            if r.receipt_date and start_date <= r.receipt_date.date() <= end_date
        ]
        
        # Amount filter
        filtered_receipts = [
            r for r in filtered_receipts
            if r.total_amount and amount_range[0] <= r.total_amount <= amount_range[1]
        ]
        
        # Merchant filter
        if selected_merchants:
            filtered_receipts = [
                r for r in filtered_receipts
                if r.merchant_name in selected_merchants
            ]
        
        # Category filter
        if selected_categories:
            filtered_receipts = [
                r for r in filtered_receipts
                if r.category in selected_categories
            ]
        
        # Display results summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Receipts", len(filtered_receipts))
        
        with col2:
            total_amount = sum(r.total_amount for r in filtered_receipts if r.total_amount)
            st.metric("💵 Total Amount", f"${total_amount:.2f}")
        
        with col3:
            avg_amount = total_amount / len(filtered_receipts) if filtered_receipts else 0
            st.metric("📈 Average Amount", f"${avg_amount:.2f}")
        
        with col4:
            unique_merchants = len(set(r.merchant_name for r in filtered_receipts if r.merchant_name))
            st.metric("🏪 Unique Merchants", unique_merchants)
        
        if not filtered_receipts:
            st.warning("🔍 No receipts match your current filters. Try adjusting your search criteria.")
            return
        
        # Display options
        st.subheader("📋 Display Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            view_mode = st.selectbox(
                "View Mode",
                ["Table", "Cards", "Detailed"]
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort By",
                ["Date (Newest)", "Date (Oldest)", "Amount (High)", "Amount (Low)", "Merchant"]
            )
        
        with col3:
            items_per_page = st.selectbox(
                "Items per Page",
                [10, 25, 50, 100],
                index=1
            )
        
        # Sort receipts
        if sort_by == "Date (Newest)":
            filtered_receipts.sort(key=lambda x: x.receipt_date or datetime.min, reverse=True)
        elif sort_by == "Date (Oldest)":
            filtered_receipts.sort(key=lambda x: x.receipt_date or datetime.min)
        elif sort_by == "Amount (High)":
            filtered_receipts.sort(key=lambda x: x.total_amount or 0, reverse=True)
        elif sort_by == "Amount (Low)":
            filtered_receipts.sort(key=lambda x: x.total_amount or 0)
        elif sort_by == "Merchant":
            filtered_receipts.sort(key=lambda x: x.merchant_name or "")
        
        # Pagination
        total_pages = (len(filtered_receipts) - 1) // items_per_page + 1
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.selectbox(
                    f"Page (1-{total_pages})",
                    range(1, total_pages + 1),
                    format_func=lambda x: f"Page {x} of {total_pages}"
                )
        else:
            page = 1
        
        # Calculate pagination
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_receipts))
        page_receipts = filtered_receipts[start_idx:end_idx]
        
        # Display receipts based on view mode
        if view_mode == "Table":
            display_table_view(page_receipts)
        elif view_mode == "Cards":
            display_card_view(page_receipts)
        else:  # Detailed
            display_detailed_view(page_receipts)
        
        # Bulk actions
        st.subheader("🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Export Filtered Data", type="secondary"):
                export_receipts(filtered_receipts)
        
        with col2:
            if st.button("🗑️ Delete Selected", type="secondary"):
                st.info("🚧 Coming Soon: Bulk delete functionality!")
        
        with col3:
            if st.button("🏷️ Bulk Categorize", type="secondary"):
                st.info("🚧 Coming Soon: Bulk categorization!")
    
    except Exception as e:
        logger.error(f"Error in data explorer: {e}")
        st.error(f"❌ Error loading data: {str(e)}")

def display_table_view(receipts):
    """Display receipts in table format"""
    if not receipts:
        return
    
    # Create DataFrame
    data = []
    for receipt in receipts:
        data.append({
            'Date': receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else 'Unknown',
            'Merchant': receipt.merchant_name or 'Unknown',
            'Amount': f"${receipt.total_amount:.2f}" if receipt.total_amount else '$0.00',
            'Items': len(receipt.items),
            'Category': receipt.category or 'Uncategorized',
            'Filename': receipt.filename
        })
    
    df = pd.DataFrame(data)
    
    # Display with selection capability
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row"
    )
    
    # Handle selection
    if event.selection.rows:
        selected_receipts = [receipts[i] for i in event.selection.rows]
        st.success(f"✅ Selected {len(selected_receipts)} receipts")
        
        # Show quick actions for selected receipts
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 View Details"):
                for receipt in selected_receipts[:3]:  # Limit to 3 for display
                    with st.expander(f"{receipt.filename}"):
                        display_receipt_details(receipt)
        
        with col2:
            if st.button("📤 Export Selected"):
                export_receipts(selected_receipts)
        
        with col3:
            total_selected = sum(r.total_amount for r in selected_receipts if r.total_amount)
            st.metric("Selected Total", f"${total_selected:.2f}")

def display_card_view(receipts):
    """Display receipts in card format"""
    cols = st.columns(2)
    
    for i, receipt in enumerate(receipts):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <h4>{receipt.merchant_name or 'Unknown Merchant'}</h4>
                    <p><strong>Date:</strong> {receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else 'Unknown'}</p>
                    <p><strong>Amount:</strong> ${receipt.total_amount:.2f if receipt.total_amount else 0:.2f}</p>
                    <p><strong>Items:</strong> {len(receipt.items)}</p>
                    <p><strong>Category:</strong> {receipt.category or 'Uncategorized'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Details", key=f"card_{receipt.id}"):
                    with st.expander("Receipt Details", expanded=True):
                        display_receipt_details(receipt)

def display_detailed_view(receipts):
    """Display receipts in detailed format"""
    for receipt in receipts:
        with st.expander(f"{receipt.merchant_name or 'Unknown'} - {receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else 'Unknown'} - ${receipt.total_amount:.2f if receipt.total_amount else 0:.2f}"):
            display_receipt_details(receipt)

def display_receipt_details(receipt):
    """Display detailed information for a single receipt"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Receipt Information")
        st.write(f"**Filename:** {receipt.filename}")
        st.write(f"**Merchant:** {receipt.merchant_name or 'Unknown'}")
        st.write(f"**Date:** {receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else 'Unknown'}")
        st.write(f"**Amount:** ${receipt.total_amount:.2f if receipt.total_amount else 0:.2f}")
        st.write(f"**Category:** {receipt.category or 'Uncategorized'}")
        st.write(f"**Upload Date:** {receipt.upload_date.strftime('%Y-%m-%d %H:%M')}")
        
        if receipt.notes:
            st.write(f"**Notes:** {receipt.notes}")
    
    with col2:
        st.subheader("🛍️ Items")
        if receipt.items:
            items_data = []
            for item in receipt.items:
                items_data.append({
                    'Item': item.name,
                    'Quantity': item.quantity,
                    'Price': f"${item.price:.2f}",
                    'Category': item.category or 'N/A'
                })
            
            items_df = pd.DataFrame(items_data)
            st.dataframe(items_df, use_container_width=True, hide_index=True)
        else:
            st.info("No items extracted from this receipt")
    
    # Raw text
    st.subheader("📄 Raw Text")
    st.text_area("", receipt.raw_text, height=150, disabled=True, key=f"raw_text_{receipt.id}")
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Delete", key=f"delete_{receipt.id}", type="secondary"):
            if st.session_state.db_manager.delete_receipt(receipt.id):
                st.success("✅ Receipt deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to delete receipt")
    
    with col2:
        if st.button("✏️ Edit", key=f"edit_{receipt.id}", type="secondary"):
            st.info("🚧 Edit functionality coming soon!")
    
    with col3:
        if st.button("📤 Export", key=f"export_{receipt.id}", type="secondary"):
            export_receipts([receipt])

def export_receipts(receipts):
    """Export receipts to CSV"""
    if not receipts:
        st.warning("No receipts to export")
        return
    
    # Prepare export data
    export_data = []
    for receipt in receipts:
        export_data.append({
            'filename': receipt.filename,
            'merchant': receipt.merchant_name or '',
            'date': receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else '',
            'amount': receipt.total_amount or 0,
            'category': receipt.category or '',
            'items_count': len(receipt.items),
            'notes': receipt.notes or '',
            'raw_text': receipt.raw_text
        })
    
    # Create CSV
    df = pd.DataFrame(export_data)
    csv = df.to_csv(index=False)
    
    # Download button
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"receipts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.success(f"✅ Prepared {len(receipts)} receipts for export!")

if __name__ == "__main__":
    main()
