# Receipt Processing Application

A professional full-stack receipt processing application built with Python and Streamlit that extracts structured data from various file formats and provides comprehensive analytical insights.

## 🚀 Features

### Core Functionality
- **Multi-format Support**: Process PDFs, images (JPG, PNG, TIFF, BMP)
- **Advanced OCR**: Hybrid text extraction using PyMuPDF and Tesseract
- **Intelligent Data Extraction**: Automatic vendor, date, amount, and category detection
- **Data Validation**: Comprehensive validation using Pydantic models
- **Database Management**: SQLite with proper indexing and ACID compliance

### User Interface
- **Multi-page Architecture**: Streamlit-based responsive web interface
- **Interactive Analytics**: Comprehensive dashboards with Plotly visualizations
- **Manual Correction**: Inline editing for extracted data
- **Search & Filter**: Advanced search with fuzzy matching
- **Data Export**: CSV and JSON export capabilities

### Advanced Features
- **Image Preprocessing**: Perspective correction, noise removal, binarization
- **Pattern Detection**: Spending anomalies and duplicate receipt detection
- **Trend Analysis**: Time-based spending patterns and seasonal insights
- **Vendor Loyalty**: Analysis of vendor relationships and spending habits
- **Currency Support**: Multi-currency detection and handling

## 🏗️ Architecture

### Project Structure
\`\`\`
receipt-processor/
├── src/
│   ├── app.py                 # Main Streamlit application
│   ├── core/                  # Backend logic modules
│   │   ├── models.py          # Pydantic data models
│   │   ├── parsing.py         # File processing & OCR
│   │   ├── database.py        # Database layer (SQLite)
│   │   └── algorithms.py      # Search & analytics algorithms
│   ├── pages/                 # Streamlit pages
│   │   ├── 1_Data_Explorer.py # Data management interface
│   │   └── 2_Analytics_Dashboard.py # Analytics & visualizations
│   └── ui/                    # UI components
│       └── components.py      # Reusable UI components
├── tests/                     # Test files
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
└── README.md                 # This file
\`\`\`

### Technology Stack
- **Frontend**: Streamlit with multi-page architecture
- **Backend**: Python with modular design
- **Database**: SQLite with proper indexing
- **OCR**: PyMuPDF (text-based PDFs) + Tesseract (images)
- **Image Processing**: OpenCV for preprocessing
- **Data Validation**: Pydantic models
- **Visualizations**: Plotly for interactive charts
- **Data Processing**: Pandas for analytics

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Tesseract OCR engine

### Install Tesseract OCR

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH

**macOS:**
\`\`\`bash
brew install tesseract
\`\`\`

**Ubuntu/Debian:**
\`\`\`bash
sudo apt-get update
sudo apt-get install tesseract-ocr
\`\`\`

### Application Setup

1. **Clone the repository:**
\`\`\`bash
git clone <repository-url>
cd receipt-processor
\`\`\`

2. **Create virtual environment:**
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

3. **Install dependencies:**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. **Run the application:**
\`\`\`bash
streamlit run src/app.py
\`\`\`

5. **Access the application:**
Open your browser and navigate to `http://localhost:8501`

## 📖 Usage Guide

### 1. Upload Receipts
- Navigate to the **Data Explorer** page
- Use the file uploader to select receipt files
- Supported formats: PDF, JPG, PNG, TIFF, BMP (max 10MB)
- Review and correct extracted data before saving

### 2. Search & Filter
- Use the search interface to find specific receipts
- Filter by vendor, date range, amount, category, or currency
- Enable fuzzy search for similar vendor names
- Sort results by various criteria

### 3. Edit Receipts
- Select receipts for manual correction
- Update vendor names, amounts, dates, and categories
- View original extracted text for reference
- Save changes to update the database

### 4. Analytics Dashboard
- **Overview**: Key metrics and quick insights
- **Spending Analysis**: Detailed breakdowns by vendor and category
- **Time Trends**: Seasonal patterns and spending trends
- **Advanced Insights**: Anomaly detection and duplicate identification

### 5. Export Data
- Export filtered results as CSV or JSON
- Download files with timestamp-based naming
- Preserve all receipt metadata in exports

## 🚀 Deployment

### Railway Deployment
This application is configured for Railway deployment with:
- `nixpacks.toml` for build configuration
- `Procfile` for start command
- Automatic Tesseract OCR installation

### Other Platforms
- **Streamlit Cloud**: Direct GitHub integration
- **Heroku**: Python buildpack support
- **Docker**: Containerized deployment ready

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
\`\`\`env
# Database configuration
DATABASE_PATH=receipts.db

# OCR configuration
TESSERACT_CMD=/usr/bin/tesseract  # Path to tesseract executable

# Logging level
LOG_LEVEL=INFO
\`\`\`

### Customization Options
- **Categories**: Modify `CategoryEnum` in `models.py`
- **Currencies**: Update `CurrencyEnum` for additional currencies
- **OCR Settings**: Adjust Tesseract configuration in `parsing.py`
- **UI Styling**: Customize CSS in Streamlit components

## 🧪 Testing

Run the test suite:
\`\`\`bash
python -m pytest tests/ -v
\`\`\`

Test coverage:
\`\`\`bash
python -m pytest tests/ --cov=src --cov-report=html
\`\`\`

## 📊 Performance Considerations

### Database Optimization
- Indexed columns for fast queries
- Parameterized queries to prevent SQL injection
- Connection pooling for concurrent access

### Image Processing
- Optimized preprocessing pipeline
- Memory-efficient operations
- Batch processing capabilities

### OCR Accuracy
- Image enhancement techniques
- Multiple extraction patterns
- Confidence scoring and validation

## 🚧 Limitations & Assumptions

### Current Limitations
- Single-page receipt processing only
- English language OCR primarily
- Limited to common receipt formats
- No real-time processing

### Assumptions
- Receipts contain standard information (vendor, date, amount)
- Images are reasonably clear and well-lit
- PDF files are not password-protected
- Amounts are in decimal format

## 🛣️ Future Enhancements

### Planned Features
- **Batch Processing**: Multiple file upload and processing
- **Multi-language Support**: Additional OCR language packs
- **Cloud Storage**: Integration with cloud storage services
- **Mobile App**: React Native mobile application
- **API Endpoints**: RESTful API for external integrations
- **Machine Learning**: Improved categorization with ML models

### Technical Improvements
- **Caching**: Redis for improved performance
- **Async Processing**: Background task processing
- **Microservices**: Service-oriented architecture
- **Docker**: Containerized deployment
- **CI/CD**: Automated testing and deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit** for the excellent web framework
- **Tesseract OCR** for optical character recognition
- **PyMuPDF** for PDF text extraction
- **OpenCV** for image processing capabilities
- **Plotly** for interactive visualizations

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review existing issues for solutions

---

**Built with ❤️ using Python, Streamlit, and modern web technologies**
\`\`\`
