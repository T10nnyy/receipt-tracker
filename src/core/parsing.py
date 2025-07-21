import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import cv2
import numpy as np
import pytesseract
import fitz  # PyMuPDF
from pathlib import Path
import io

from .models import ReceiptItem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextExtractor:
    """Extracts and processes text from receipt images and PDFs"""
    
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/$-: '
        
        # Common patterns for receipt parsing
        self.patterns = {
            'total': [
                r'total[:\s]*\$?(\d+\.?\d*)',
                r'amount[:\s]*\$?(\d+\.?\d*)',
                r'sum[:\s]*\$?(\d+\.?\d*)',
                r'\$(\d+\.\d{2})\s*$'
            ],
            'date': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}',
                r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}'
            ],
            'merchant': [
                r'^([A-Z][A-Za-z\s&]+)(?=\n|\r)',
                r'([A-Z][A-Za-z\s&]{3,})\s*(?:store|shop|market|restaurant|cafe)',
            ],
            'items': [
                r'([A-Za-z][A-Za-z\s]+)\s+(\d+\.?\d*)\s*\$?(\d+\.\d{2})',
                r'([A-Za-z][A-Za-z\s]+)\s+\$?(\d+\.\d{2})',
            ]
        }
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text and information from a file (image or PDF)"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'success': False, 'error': 'File not found'}
            
            # Determine file type and extract text
            if file_path.suffix.lower() == '.pdf':
                text = self._extract_from_pdf(file_path)
            else:
                text = self._extract_from_image(file_path)
            
            if not text.strip():
                return {'success': False, 'error': 'No text could be extracted'}
            
            # Parse extracted text
            parsed_data = self._parse_receipt_text(text)
            
            return {
                'success': True,
                'text': text,
                **parsed_data
            }
            
        except Exception as e:
            logger.error(f"Error extracting from file {file_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_from_image(self, image_path: Path) -> str:
        """Extract text from image using OCR"""
        try:
            # Load and preprocess image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Could not load image")
            
            processed_image = self.preprocess_image(image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise
    
    def _extract_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        try:
            text = ""
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Try text extraction first
                page_text = page.get_text()
                
                if page_text.strip():
                    text += page_text + "\n"
                else:
                    # If no text, try OCR on page image
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Convert PIL to OpenCV format
                    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    processed_img = self.preprocess_image(img_cv)
                    
                    ocr_text = pytesseract.image_to_string(processed_img, config=self.tesseract_config)
                    text += ocr_text + "\n"
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Resize if image is too small
            height, width = cleaned.shape
            if height < 300 or width < 300:
                scale_factor = max(300 / height, 300 / width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image
    
    def _parse_receipt_text(self, text: str) -> Dict[str, Any]:
        """Parse receipt text to extract structured information"""
        result = {
            'total_amount': None,
            'merchant_name': None,
            'date': None,
            'items': []
        }
        
        try:
            # Clean text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text_lower = text.lower()
            
            # Extract total amount
            result['total_amount'] = self._extract_total(text_lower)
            
            # Extract merchant name
            result['merchant_name'] = self._extract_merchant(lines)
            
            # Extract date
            result['date'] = self._extract_date(text)
            
            # Extract items
            result['items'] = self._extract_items(lines)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing receipt text: {e}")
            return result
    
    def _extract_total(self, text: str) -> Optional[float]:
        """Extract total amount from text"""
        for pattern in self.patterns['total']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Get the last match (usually the final total)
                    amount_str = matches[-1].replace('$', '').replace(',', '')
                    return float(amount_str)
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_merchant(self, lines: List[str]) -> Optional[str]:
        """Extract merchant name from text lines"""
        # Usually the merchant name is in the first few lines
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 3 and not re.match(r'^\d', line):
                # Clean up common receipt artifacts
                cleaned = re.sub(r'[^\w\s&-]', '', line)
                if len(cleaned) > 3:
                    return cleaned.title()
        return None
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from text"""
        for pattern in self.patterns['date']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Try different date formats
                        date_str = match if isinstance(match, str) else match[0]
                        
                        # Common date formats
                        formats = [
                            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
                            '%Y/%m/%d', '%Y-%m-%d',
                            '%d/%m/%Y', '%d-%m-%Y',
                            '%B %d, %Y', '%b %d, %Y',
                            '%d %B %Y', '%d %b %Y'
                        ]
                        
                        for fmt in formats:
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                                
                    except Exception:
                        continue
        return None
    
    def _extract_items(self, lines: List[str]) -> List[ReceiptItem]:
        """Extract individual items from receipt lines"""
        items = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Look for patterns like "Item Name 1.99" or "Item Name 2 $3.98"
            patterns = [
                r'^([A-Za-z][A-Za-z\s]+?)\s+(\d+)\s*\$?(\d+\.\d{2})$',  # Item Qty Price
                r'^([A-Za-z][A-Za-z\s]+?)\s+\$?(\d+\.\d{2})$',  # Item Price
                r'^([A-Za-z][A-Za-z\s]+?)\s+(\d+\.\d{2})\s*$',  # Item Price (no $)
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 3:  # Item, Qty, Price
                        name, qty, price = groups
                        try:
                            items.append(ReceiptItem(
                                name=name.strip().title(),
                                quantity=int(qty),
                                price=float(price)
                            ))
                            break
                        except ValueError:
                            continue
                    
                    elif len(groups) == 2:  # Item, Price
                        name, price = groups
                        try:
                            items.append(ReceiptItem(
                                name=name.strip().title(),
                                quantity=1,
                                price=float(price)
                            ))
                            break
                        except ValueError:
                            continue
        
        return items
