"""
File processing and text extraction module.
Implements hybrid OCR approach with image preprocessing and intelligent text extraction.
"""

import cv2
import numpy as np
import pytesseract
import fitz  # PyMuPDF
import re
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from PIL import Image
import io
import time

from .models import Receipt, ProcessingResult, CategoryEnum, CurrencyEnum


class TextExtractor:
    """
    Advanced text extraction with OCR and PDF parsing capabilities.
    
    Implements intelligent preprocessing, multi-format support,
    and robust data extraction algorithms.
    """
    
    def __init__(self):
        """Initialize text extractor with configuration."""
        self.logger = logging.getLogger(__name__)
        
        # OCR configuration
        self.tesseract_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/$-: '
        
        # Regex patterns for data extraction
        self.amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $123.45, $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 123.45$
            r'TOTAL[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # TOTAL: $123.45
            r'AMOUNT[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # AMOUNT: 123.45
            r'(\d{1,3}(?:,\d{3})*\.\d{2})',  # Generic decimal amounts
        ]
        
        self.date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY, MM-DD-YY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',    # YYYY/MM/DD
            r'(\w{3,9}\s+\d{1,2},?\s+\d{4})',    # January 1, 2024
            r'(\d{1,2}\s+\w{3,9}\s+\d{4})',      # 1 January 2024
        ]
        
        # Currency symbols and patterns
        self.currency_patterns = {
            CurrencyEnum.USD: [r'\$', r'USD', r'US\$'],
            CurrencyEnum.EUR: [r'€', r'EUR', r'EURO'],
            CurrencyEnum.GBP: [r'£', r'GBP', r'POUND'],
            CurrencyEnum.CAD: [r'CAD', r'C\$'],
            CurrencyEnum.AUD: [r'AUD', r'A\$'],
        }
        
        # Category keywords for automatic classification
        self.category_keywords = {
            CategoryEnum.FOOD: ['restaurant', 'cafe', 'diner', 'bistro', 'grill', 'pizza', 'burger', 'food'],
            CategoryEnum.GROCERIES: ['grocery', 'supermarket', 'market', 'walmart', 'target', 'costco', 'safeway'],
            CategoryEnum.TRANSPORTATION: ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'parking', 'metro', 'bus'],
            CategoryEnum.ENTERTAINMENT: ['movie', 'theater', 'cinema', 'concert', 'show', 'entertainment'],
            CategoryEnum.SHOPPING: ['store', 'shop', 'mall', 'retail', 'amazon', 'ebay'],
            CategoryEnum.UTILITIES: ['electric', 'water', 'gas', 'internet', 'phone', 'utility'],
            CategoryEnum.HEALTHCARE: ['pharmacy', 'hospital', 'clinic', 'doctor', 'medical', 'health'],
            CategoryEnum.BUSINESS: ['office', 'supplies', 'business', 'professional', 'service'],
        }
    
    def process_file(self, file_path: str, filename: str) -> ProcessingResult:
        """
        Process uploaded file and extract receipt data.
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            ProcessingResult with extracted receipt or error information
        """
        start_time = time.time()
        
        try:
            file_path = Path(file_path)
            file_extension = file_path.suffix.lower()
            
            self.logger.info(f"Processing file: {filename} ({file_extension})")
            
            # Route to appropriate processor
            if file_extension == '.pdf':
                text, confidence = self._process_pdf(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                text, confidence = self._process_image(file_path)
            else:
                return ProcessingResult(
                    success=False,
                    error_message=f"Unsupported file format: {file_extension}"
                )
            
            if not text.strip():
                return ProcessingResult(
                    success=False,
                    error_message="No text could be extracted from the file"
                )
            
            # Extract structured data from text
            receipt_data = self._extract_receipt_data(text, filename)
            receipt_data.extracted_text = text
            receipt_data.confidence_score = confidence
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                receipt=receipt_data,
                processing_time=processing_time,
                warnings=self._generate_warnings(receipt_data, confidence)
            )
            
        except Exception as e:
            self.logger.error(f"Error processing file {filename}: {e}")
            return ProcessingResult(
                success=False,
                error_message=f"Processing failed: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _process_pdf(self, file_path: Path) -> Tuple[str, float]:
        """
        Extract text from PDF using PyMuPDF with OCR fallback.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            doc = fitz.open(file_path)
            text = ""
            confidence = 100.0  # High confidence for direct text extraction
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                if page_text.strip():
                    # Direct text extraction successful
                    text += page_text + "\n"
                else:
                    # Fallback to OCR for scanned PDFs
                    self.logger.info(f"Using OCR for PDF page {page_num + 1}")
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    
                    # Convert to PIL Image for processing
                    pil_image = Image.open(io.BytesIO(img_data))
                    
                    # Preprocess and OCR
                    processed_image = self._preprocess_image(np.array(pil_image))
                    ocr_text, ocr_confidence = self._perform_ocr(processed_image)
                    
                    text += ocr_text + "\n"
                    confidence = min(confidence, ocr_confidence)  # Use lowest confidence
            
            doc.close()
            return text.strip(), confidence
            
        except Exception as e:
            self.logger.error(f"PDF processing failed: {e}")
            raise
    
    def _process_image(self, file_path: Path) -> Tuple[str, float]:
        """
        Extract text from image using OCR with preprocessing.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Load image
            image = cv2.imread(str(file_path))
            if image is None:
                raise ValueError("Could not load image file")
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Perform OCR
            text, confidence = self._perform_ocr(processed_image)
            
            return text, confidence
            
        except Exception as e:
            self.logger.error(f"Image processing failed: {e}")
            raise
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Advanced image preprocessing for optimal OCR results.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Resize if image is too small
            height, width = gray.shape
            if height < 300 or width < 300:
                scale_factor = max(300 / height, 300 / width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Adaptive thresholding for binarization
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Perspective correction (basic skew correction)
            cleaned = self._correct_skew(cleaned)
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Image preprocessing failed: {e}")
            return image  # Return original if preprocessing fails
    
    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """
        Correct image skew using Hough line detection.
        
        Args:
            image: Binary image
            
        Returns:
            Skew-corrected image
        """
        try:
            # Detect lines using Hough transform
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
            
            if lines is not None and len(lines) > 0:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:10]:  # Use first 10 lines
                    angle = theta * 180 / np.pi - 90
                    angles.append(angle)
                
                if angles:
                    median_angle = np.median(angles)
                    
                    # Only correct if skew is significant (> 1 degree)
                    if abs(median_angle) > 1:
                        height, width = image.shape
                        center = (width // 2, height // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        corrected = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                                 flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                        return corrected
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Skew correction failed: {e}")
            return image
    
    def _perform_ocr(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Perform OCR on preprocessed image.
        
        Args:
            image: Preprocessed image
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Get OCR data with confidence scores
            data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
            
            # Extract text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    text_parts.append(word)
                    conf = data['conf'][i]
                    if conf > 0:  # Valid confidence score
                        confidences.append(conf)
            
            text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return text, avg_confidence
            
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            # Fallback to simple OCR
            try:
                text = pytesseract.image_to_string(image, config=self.tesseract_config)
                return text, 50.0  # Default confidence for fallback
            except:
                return "", 0.0
    
    def _extract_receipt_data(self, text: str, filename: str) -> Receipt:
        """
        Extract structured receipt data from raw text.
        
        Args:
            text: Raw extracted text
            filename: Original filename
            
        Returns:
            Receipt object with extracted data
        """
        # Extract vendor (heuristic: first meaningful line)
        vendor = self._extract_vendor(text)
        
        # Extract transaction date
        transaction_date = self._extract_date(text)
        
        # Extract amount
        amount = self._extract_amount(text)
        
        # Detect currency
        currency = self._detect_currency(text)
        
        # Classify category
        category = self._classify_category(text, vendor)
        
        return Receipt(
            vendor=vendor,
            transaction_date=transaction_date,
            amount=amount,
            category=category,
            currency=currency,
            source_file=filename,
            extracted_text="",  # Will be set by caller
            confidence_score=0.0  # Will be set by caller
        )
    
    def _extract_vendor(self, text: str) -> str:
        """Extract vendor name from text using heuristics."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return "Unknown Vendor"
        
        # Look for the first substantial line (likely vendor name)
        for line in lines[:5]:  # Check first 5 lines
            # Skip lines that look like addresses, dates, or amounts
            if (len(line) > 3 and 
                not re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line) and
                not re.search(r'\$\d+', line) and
                not re.search(r'^\d+\s+\w+\s+(st|ave|rd|blvd|street|avenue|road|boulevard)', line, re.I)):
                
                # Clean up the vendor name
                vendor = re.sub(r'[^\w\s\-&.,]', '', line)
                vendor = re.sub(r'\s+', ' ', vendor).strip()
                
                if len(vendor) >= 2:
                    return vendor[:200]  # Limit length
        
        # Fallback to first line
        return lines[0][:200] if lines else "Unknown Vendor"
    
    def _extract_date(self, text: str) -> date:
        """Extract transaction date from text."""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try different date parsing approaches
                    parsed_date = self._parse_date_string(match)
                    if parsed_date:
                        return parsed_date
                except:
                    continue
        
        # Fallback to today's date
        return date.today()
    
    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Parse various date string formats."""
        from dateutil import parser
        
        try:
            # Use dateutil parser for flexible date parsing
            parsed = parser.parse(date_str, fuzzy=True)
            parsed_date = parsed.date()
            
            # Validate date is reasonable (not in future, not too old)
            today = date.today()
            if parsed_date <= today and parsed_date.year >= 1990:
                return parsed_date
                
        except:
            pass
        
        return None
    
    def _extract_amount(self, text: str) -> Decimal:
        """Extract transaction amount from text."""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean and convert amount
                    amount_str = match.replace(',', '').replace('$', '').strip()
                    amount = Decimal(amount_str)
                    
                    # Filter reasonable amounts (between $0.01 and $99,999.99)
                    if Decimal('0.01') <= amount <= Decimal('99999.99'):
                        amounts.append(amount)
                        
                except (InvalidOperation, ValueError):
                    continue
        
        if amounts:
            # Return the largest amount found (likely the total)
            return max(amounts)
        
        # Fallback: look for any decimal number
        decimal_matches = re.findall(r'\b(\d+\.\d{2})\b', text)
        for match in decimal_matches:
            try:
                amount = Decimal(match)
                if Decimal('0.01') <= amount <= Decimal('99999.99'):
                    amounts.append(amount)
            except:
                continue
        
        return max(amounts) if amounts else Decimal('0.01')
    
    def _detect_currency(self, text: str) -> CurrencyEnum:
        """Detect currency from text."""
        text_upper = text.upper()
        
        for currency, patterns in self.currency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    return currency
        
        # Default to USD
        return CurrencyEnum.USD
    
    def _classify_category(self, text: str, vendor: str) -> CategoryEnum:
        """Automatically classify receipt category based on text and vendor."""
        text_lower = (text + " " + vendor).lower()
        
        # Score each category based on keyword matches
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of each keyword
                score += text_lower.count(keyword)
            
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return CategoryEnum.OTHER
    
    def _generate_warnings(self, receipt: Receipt, confidence: float) -> List[str]:
        """Generate warnings based on extraction quality."""
        warnings = []
        
        if confidence < 70:
            warnings.append(f"Low OCR confidence ({confidence:.1f}%). Please verify extracted data.")
        
        if receipt.vendor == "Unknown Vendor":
            warnings.append("Could not identify vendor name. Please update manually.")
        
        if receipt.amount <= Decimal('0.01'):
            warnings.append("Amount appears unusually low. Please verify.")
        
        if receipt.transaction_date == date.today():
            warnings.append("Date defaulted to today. Please verify transaction date.")
        
        return warnings
