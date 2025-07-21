"""
File Processing and OCR Module - Advanced Text Extraction

This module implements comprehensive file processing capabilities with hybrid OCR
approach using PyMuPDF for text-based PDFs and Tesseract for images. Includes
advanced image preprocessing, pattern recognition, and data extraction algorithms.

Features:
- Multi-format file support (PDF, images, text)
- Advanced image preprocessing pipeline
- Hybrid OCR with fallback mechanisms
- Intelligent data extraction using regex patterns
- Confidence scoring and validation
- Error handling and recovery

Author: Receipt Processing Team
Version: 1.0.0
"""

import os
import re
import tempfile
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import cv2
import numpy as np
import pytesseract
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
from dateutil import parser as date_parser

from .models import Receipt, ProcessingResult, CategoryEnum, CurrencyEnum, classify_category, detect_currency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextExtractor:
    """
    Advanced text extraction engine with hybrid OCR capabilities.
    
    Implements intelligent file processing with automatic format detection,
    image preprocessing, and optimized text extraction for maximum accuracy.
    """
    
    def __init__(self):
        """Initialize the text extractor with default configurations."""
        self.supported_formats = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.txt'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # OCR configuration
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/$€£¥-: '
        
        # Regex patterns for data extraction
        self.amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $123.45, $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 123.45$
            r'TOTAL[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # TOTAL: $123.45
            r'AMOUNT[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # AMOUNT: 123.45
            r'(\d{1,3}(?:,\d{3})*\.\d{2})',  # Generic decimal amounts
        ]
        
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY, MM-DD-YY
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY/MM/DD
            r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b',  # Month DD, YYYY
            r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',    # DD Month YYYY
        ]
        
        self.vendor_stop_words = {
            'receipt', 'invoice', 'bill', 'total', 'amount', 'date', 'time',
            'thank', 'you', 'visit', 'again', 'store', 'location', 'address'
        }
    
    def process_file(self, file_path: str, filename: str) -> ProcessingResult:
        """
        Process uploaded file and extract receipt data.
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            ProcessingResult with extracted receipt data or error information
        """
        start_time = datetime.now()
        
        try:
            # Validate file
            if not self._validate_file(file_path, filename):
                return ProcessingResult(
                    success=False,
                    error_message="File validation failed"
                )
            
            # Extract text based on file type
            file_extension = Path(filename).suffix.lower()
            
            if file_extension == '.pdf':
                text, confidence = self._process_pdf(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                text, confidence = self._process_image(file_path)
            elif file_extension == '.txt':
                text, confidence = self._process_text_file(file_path)
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
            
            # Extract structured data
            receipt = self._extract_receipt_data(text, filename)
            receipt.confidence_score = confidence
            receipt.extracted_text = text
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=True,
                receipt=receipt,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Processing failed for {filename}: {e}")
            return ProcessingResult(
                success=False,
                error_message=f"Processing error: {str(e)}"
            )
    
    def _validate_file(self, file_path: str, filename: str) -> bool:
        """Validate file format and size."""
        try:
            # Check file extension
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.supported_formats:
                logger.error(f"Unsupported file format: {file_extension}")
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes")
                return False
            
            # Check if file exists and is readable
            if not os.path.isfile(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False
    
    def _process_pdf(self, file_path: str) -> Tuple[str, float]:
        """
        Process PDF file with hybrid text extraction.
        
        First attempts direct text extraction, falls back to OCR if needed.
        """
        try:
            doc = fitz.open(file_path)
            text = ""
            confidence = 1.0  # High confidence for direct text extraction
            
            # Try direct text extraction first
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text += page_text + "\n"
            
            doc.close()
            
            # If direct extraction yields little text, try OCR
            if len(text.strip()) < 50:
                logger.info("Direct PDF text extraction yielded little text, trying OCR")
                text, confidence = self._pdf_to_ocr(file_path)
            
            return text, confidence
            
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            # Fallback to OCR
            return self._pdf_to_ocr(file_path)
    
    def _pdf_to_ocr(self, file_path: str) -> Tuple[str, float]:
        """Convert PDF to images and perform OCR."""
        try:
            doc = fitz.open(file_path)
            text = ""
            confidences = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Save to temporary file for OCR
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_file.write(img_data)
                    temp_path = temp_file.name
                
                try:
                    # Perform OCR on the image
                    page_text, page_confidence = self._process_image(temp_path)
                    text += page_text + "\n"
                    confidences.append(page_confidence)
                finally:
                    os.unlink(temp_path)
            
            doc.close()
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"PDF OCR processing error: {e}")
            return "", 0.0
    
    def _process_image(self, file_path: str) -> Tuple[str, float]:
        """
        Process image file with advanced preprocessing and OCR.
        
        Applies image enhancement techniques for optimal OCR accuracy.
        """
        try:
            # Load and preprocess image
            processed_image = self._preprocess_image(file_path)
            
            # Perform OCR with confidence scoring
            ocr_data = pytesseract.image_to_data(
                processed_image,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and calculate confidence
            text_parts = []
            confidences = []
            
            for i, word in enumerate(ocr_data['text']):
                if word.strip():
                    text_parts.append(word)
                    conf = int(ocr_data['conf'][i])
                    if conf > 0:  # Only include positive confidence scores
                        confidences.append(conf)
            
            text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return "", 0.0
    
    def _preprocess_image(self, file_path: str) -> np.ndarray:
        """
        Advanced image preprocessing pipeline for optimal OCR.
        
        Applies perspective correction, noise removal, and enhancement techniques.
        """
        try:
            # Load image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError("Could not load image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply perspective correction if needed
            corrected = self._correct_perspective(gray)
            
            # Noise removal
            denoised = cv2.medianBlur(corrected, 3)
            
            # Adaptive thresholding for better text contrast
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up text
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Enhance contrast
            enhanced = cv2.convertScaleAbs(cleaned, alpha=1.2, beta=10)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            # Return original image if preprocessing fails
            return cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    
    def _correct_perspective(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct perspective distortion in receipt images.
        
        Uses edge detection and contour analysis to find receipt boundaries.
        """
        try:
            # Edge detection
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find the largest rectangular contour (likely the receipt)
            for contour in sorted(contours, key=cv2.contourArea, reverse=True):
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # If we found a quadrilateral, apply perspective correction
                if len(approx) == 4:
                    return self._apply_perspective_transform(image, approx)
            
            # If no quadrilateral found, return original
            return image
            
        except Exception as e:
            logger.error(f"Perspective correction error: {e}")
            return image
    
    def _apply_perspective_transform(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """Apply perspective transformation to correct skewed receipts."""
        try:
            # Order corners: top-left, top-right, bottom-right, bottom-left
            corners = corners.reshape(4, 2)
            
            # Calculate dimensions of the corrected image
            width = max(
                np.linalg.norm(corners[0] - corners[1]),
                np.linalg.norm(corners[2] - corners[3])
            )
            height = max(
                np.linalg.norm(corners[0] - corners[3]),
                np.linalg.norm(corners[1] - corners[2])
            )
            
            # Define destination points
            dst_corners = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype=np.float32)
            
            # Calculate perspective transform matrix
            matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst_corners)
            
            # Apply transformation
            corrected = cv2.warpPerspective(image, matrix, (int(width), int(height)))
            
            return corrected
            
        except Exception as e:
            logger.error(f"Perspective transform error: {e}")
            return image
    
    def _process_text_file(self, file_path: str) -> Tuple[str, float]:
        """Process plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text, 1.0  # High confidence for direct text
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                return text, 0.9  # Slightly lower confidence
            except Exception as e:
                logger.error(f"Text file processing error: {e}")
                return "", 0.0
        except Exception as e:
            logger.error(f"Text file processing error: {e}")
            return "", 0.0
    
    def _extract_receipt_data(self, text: str, filename: str) -> Receipt:
        """
        Extract structured receipt data from text using pattern matching.
        
        Uses regex patterns and heuristics to identify vendor, date, amount, and category.
        """
        # Extract vendor (usually in the first few lines)
        vendor = self._extract_vendor(text)
        
        # Extract transaction date
        transaction_date = self._extract_date(text)
        
        # Extract amount
        amount = self._extract_amount(text)
        
        # Classify category
        category = classify_category(text, vendor)
        
        # Detect currency
        currency = detect_currency(text)
        
        return Receipt(
            vendor=vendor,
            transaction_date=transaction_date,
            amount=amount,
            category=category,
            currency=currency,
            source_file=filename,
            extracted_text=text,
            confidence_score=0.0  # Will be set by caller
        )
    
    def _extract_vendor(self, text: str) -> str:
        """
        Extract vendor name using heuristic analysis.
        
        Looks for vendor name in the first few lines, filtering out common receipt terms.
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return "Unknown Vendor"
        
        # Check first few lines for vendor name
        for line in lines[:5]:
            # Clean the line
            cleaned_line = re.sub(r'[^\w\s&\'-]', ' ', line)
            words = cleaned_line.lower().split()
            
            # Filter out stop words and short words
            filtered_words = [
                word for word in words 
                if len(word) > 2 and word not in self.vendor_stop_words
            ]
            
            # If we have meaningful words, this might be the vendor
            if filtered_words and len(' '.join(filtered_words)) > 3:
                vendor_name = ' '.join(word.title() for word in filtered_words)
                if len(vendor_name) <= 200:  # Respect max length
                    return vendor_name
        
        # Fallback: use first non-empty line
        return lines[0][:200] if lines[0] else "Unknown Vendor"
    
    def _extract_date(self, text: str) -> datetime:
        """
        Extract transaction date using multiple pattern matching strategies.
        
        Tries various date formats and returns the most likely transaction date.
        """
        dates_found = []
        
        # Try each date pattern
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Parse date using dateutil for flexibility
                    parsed_date = date_parser.parse(match, fuzzy=True)
                    
                    # Validate date is reasonable (not in future, not too old)
                    if parsed_date <= datetime.now() and parsed_date.year >= 2000:
                        dates_found.append(parsed_date)
                        
                except (ValueError, TypeError):
                    continue
        
        # Return the most recent valid date, or current date if none found
        if dates_found:
            return max(dates_found)
        else:
            logger.warning("No valid date found in text, using current date")
            return datetime.now()
    
    def _extract_amount(self, text: str) -> Decimal:
        """
        Extract transaction amount using pattern matching and validation.
        
        Looks for monetary amounts and returns the most likely total amount.
        """
        amounts_found = []
        
        # Try each amount pattern
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean the amount string
                    amount_str = match.replace(',', '').replace('$', '').strip()
                    amount = Decimal(amount_str)
                    
                    # Validate amount is reasonable
                    if Decimal('0.01') <= amount <= Decimal('10000.00'):
                        amounts_found.append(amount)
                        
                except (InvalidOperation, ValueError):
                    continue
        
        # Return the largest amount found (likely the total), or default
        if amounts_found:
            return max(amounts_found)
        else:
            logger.warning("No valid amount found in text, using default")
            return Decimal('0.01')  # Minimum valid amount
