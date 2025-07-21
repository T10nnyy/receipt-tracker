# Receipt Processing Application

A comprehensive receipt processing application built with Streamlit that allows users to upload, process, analyze, and manage receipt data with advanced OCR capabilities.

## Features

### 📄 Receipt Processing
- **Multi-format Support**: Process PDF files and images (PNG, JPG, JPEG)
- **Advanced OCR**: Powered by Tesseract with image preprocessing
- **Smart Data Extraction**: Automatically extracts vendor, date, amount, and items
- **Batch Processing**: Handle multiple receipts simultaneously

### 📊 Data Management
- **Interactive Data Explorer**: Search, filter, and edit receipt data
- **Advanced Search**: Fuzzy search across all receipt fields
- **Data Export**: Export filtered data to CSV format
- **Bulk Operations**: Edit multiple receipts at once

### 📈 Analytics Dashboard
- **Spending Insights**: Visualize spending patterns over time
- **Vendor Analysis**: Track spending by vendor with interactive charts
- **Category Breakdown**: Analyze expenses by category
- **Trend Analysis**: Identify spending trends and patterns

### 🔍 Smart Features
- **Duplicate Detection**: Automatically identify potential duplicate receipts
- **Pattern Recognition**: Detect unusual spending patterns
- **Data Validation**: Ensure data quality with built-in validation
- **Error Handling**: Robust error handling for file processing

## Installation

### Local Development

1. **Clone the repository**
   \`\`\`bash
   git clone <repository-url>
   cd receipt-processor
   \`\`\`

2. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Install Tesseract OCR**
   
   **Ubuntu/Debian:**
   \`\`\`bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   \`\`\`
   
   **macOS:**
   \`\`\`bash
   brew install tesseract
   \`\`\`
   
   **Windows:**
   Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

4. **Run the application**
   \`\`\`bash
   streamlit run src/app.py
   \`\`\`

### Railway Deployment

This application is configured for easy deployment on Railway:

1. **Connect Repository**: Link your GitHub repository to Railway
2. **Automatic Build**: Railway will automatically detect the configuration
3. **Environment Setup**: Tesseract OCR is automatically installed via nixpacks.toml
4. **Deploy**: The application will be available at your Railway URL

## Project Structure

\`\`\`
receipt-processor/
├── src/
│   ├── app.py                 # Main Streamlit application
│   ├── core/
│   │   ├── models.py          # Data models and validation
│   │   ├── database.py        # Database operations
│   │   ├── parsing.py         # OCR and text extraction
│   │   └── algorithms.py      # Analysis algorithms
│   ├── pages/
│   │   ├── 1_Data_Explorer.py # Data management interface
│   │   └── 2_Analytics_Dashboard.py # Analytics and insights
│   └── ui/
│       └── components.py      # Reusable UI components
├── tests/
│   ├── test_database.py       # Database tests
│   └── test_models.py         # Model validation tests
├── requirements.txt           # Python dependencies
├── nixpacks.toml             # Railway deployment config
├── Procfile                  # Process configuration
└── README.md                 # This file
\`\`\`

## Usage

### 1. Upload Receipts
- Navigate to the main page
- Upload PDF files or images using the file uploader
- The system will automatically process and extract data

### 2. Explore Data
- Use the **Data Explorer** page to view all processed receipts
- Search and filter receipts using various criteria
- Edit receipt data directly in the interface
- Export filtered data to CSV

### 3. Analyze Spending
- Visit the **Analytics Dashboard** for insights
- View spending trends over time
- Analyze vendor and category breakdowns
- Identify spending patterns and anomalies

## Technical Details

### OCR Processing
- **Image Preprocessing**: Automatic image enhancement for better OCR results
- **Multi-engine Support**: Uses both PyMuPDF and Tesseract for optimal results
- **Error Recovery**: Fallback mechanisms for challenging documents

### Database
- **SQLite Backend**: Lightweight, serverless database
- **Data Validation**: Pydantic models ensure data integrity
- **Performance**: Optimized queries for fast data retrieval

### Analytics
- **Real-time Processing**: Analytics update automatically as data changes
- **Interactive Visualizations**: Plotly-powered charts and graphs
- **Statistical Analysis**: Advanced algorithms for pattern detection

## API Reference

### Core Classes

#### `Receipt`
```python
class Receipt(BaseModel):
    id: Optional[int] = None
    vendor: str
    transaction_date: date
    amount: float
    items: List[str] = []
    category: str = "Other"
    payment_method: str = "Unknown"
    created_at: Optional[datetime] = None
