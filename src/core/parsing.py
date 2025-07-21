import re
import pytesseract
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReceiptParser:
    """OCR-based receipt parser"""
    
    def __init__(self):
        """Initialize the parser"""
        self.store_patterns = {
            'walmart': r'walmart|wal-mart',
            'target': r'target',
            'costco': r'costco',
            'kroger': r'kroger',
            'safeway': r'safeway',
            'whole foods': r'whole\s*foods',
            'trader joe': r'trader\s*joe',
            'cvs': r'cvs',
            'walgreens': r'walgreens',
            'home depot': r'home\s*depot',
            'lowes': r'lowe\'?s',
            'best buy': r'best\s*buy'
        }
        
        self.category_keywords = {
            'Grocery': ['grocery', 'food', 'produce', 'meat', 'dairy', 'bread', 'milk', 'eggs'],
            'Restaurant': ['restaurant', 'cafe', 'diner', 'pizza', 'burger', 'coffee', 'bar'],
            'Gas': ['gas', 'fuel', 'shell', 'exxon', 'bp', 'chevron', 'mobil'],
            'Retail': ['store', 'shop', 'mall', 'outlet', 'department'],
            'Pharmacy': ['pharmacy', 'drug', 'cvs', 'walgreens', 'rite aid'],
            'Home': ['home depot', 'lowes', 'hardware', 'garden', 'improvement'],
            'Electronics': ['best buy', 'electronics', 'computer', 'phone', 'tech'],
            'Clothing': ['clothing', 'apparel', 'fashion', 'shoes', 'dress']
        }
    
    def parse_image(self, image: Image.Image) -> Dict[str, Any]:
        """Parse receipt from image"""
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(processed_image, config='--psm 6')
            
            logger.info(f"Extracted text: {text[:200]}...")
            
            # Parse the extracted text
            parsed_data = self._parse_text(text)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing image: {str(e)}")
            return {
                'store_name': 'Unknown',
                'date': datetime.now(),
                'total': 0.0,
                'items': [],
                'category': 'Other'
            }
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        try:
            # Convert PIL image to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply image processing techniques
            # 1. Noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # 2. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 3. Thresholding
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(thresh)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}, using original image")
            return image
    
    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse extracted text to extract receipt information"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        parsed_data = {
            'store_name': self._extract_store_name(text),
            'date': self._extract_date(text),
            'total': self._extract_total(text),
            'items': self._extract_items(lines),
            'category': 'Other'
        }
        
        # Determine category based on store name
        parsed_data['category'] = self._determine_category(parsed_data['store_name'])
        
        return parsed_data
    
    def _extract_store_name(self, text: str) -> str:
        """Extract store name from text"""
        text_lower = text.lower()
        
        # Check for known store patterns
        for store, pattern in self.store_patterns.items():
            if re.search(pattern, text_lower):
                return store.title()
        
        # Try to extract from first few lines
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if len(line) > 3 and not re.search(r'\d', line):
                # Likely a store name if it's text without numbers
                return line.title()
        
        return 'Unknown Store'
    
    def _extract_date(self, text: str) -> datetime:
        """Extract date from text"""
        # Common date patterns
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',  # MM/DD/YYYY or MM/DD/YY
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})',  # MM-DD-YYYY or MM-DD-YY
            r'(\d{2,4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            r'(\d{2,4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    match = matches[0]
                    # Try different date formats
                    if len(match[2]) == 4:  # YYYY format
                        if int(match[2]) > 2000:  # Likely YYYY/MM/DD
                            date = datetime(int(match[2]), int(match[1]), int(match[0]))
                        else:  # MM/DD/YYYY
                            date = datetime(int(match[2]), int(match[0]), int(match[1]))
                    else:  # YY format
                        year = int(match[2])
                        if year < 50:
                            year += 2000
                        else:
                            year += 1900
                        date = datetime(year, int(match[0]), int(match[1]))
                    
                    return date
                except (ValueError, IndexError):
                    continue
        
        # If no date found, return current date
        return datetime.now()
    
    def _extract_total(self, text: str) -> float:
        """Extract total amount from text"""
        # Look for total patterns
        total_patterns = [
            r'total[:\s]*\$?(\d+\.?\d*)',
            r'amount[:\s]*\$?(\d+\.?\d*)',
            r'balance[:\s]*\$?(\d+\.?\d*)',
            r'\$(\d+\.\d{2})\s*$',  # Dollar amount at end of line
        ]
        
        text_lower = text.lower()
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text_lower, re.MULTILINE)
            if matches:
                try:
                    # Get the largest amount (likely the total)
                    amounts = [float(match) for match in matches]
                    return max(amounts)
                except ValueError:
                    continue
        
        # Look for any dollar amounts and take the largest
        dollar_amounts = re.findall(r'\$(\d+\.\d{2})', text)
        if dollar_amounts:
            try:
                amounts = [float(amount) for amount in dollar_amounts]
                return max(amounts)
            except ValueError:
                pass
        
        return 0.0
    
    def _extract_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract items from receipt lines"""
        items = []
        
        for line in lines:
            # Skip lines that are likely headers, totals, or store info
            if any(keyword in line.lower() for keyword in ['total', 'subtotal', 'tax', 'change', 'cash', 'card']):
                continue
            
            # Look for lines with prices
            price_match = re.search(r'\$?(\d+\.\d{2})', line)
            if price_match:
                price = float(price_match.group(1))
                
                # Extract item name (text before the price)
                item_name = re.sub(r'\$?\d+\.\d{2}.*', '', line).strip()
                
                # Clean up item name
                item_name = re.sub(r'^\d+\s*', '', item_name)  # Remove leading numbers
                item_name = item_name.strip()
                
                if item_name and len(item_name) > 2:
                    items.append({
                        'name': item_name,
                        'price': price,
                        'quantity': 1,
                        'category': 'Other'
                    })
        
        return items
    
    def _determine_category(self, store_name: str) -> str:
        """Determine receipt category based on store name"""
        store_lower = store_name.lower()
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in store_lower:
                    return category
        
        return 'Other'
    
    def parse_text_directly(self, text: str) -> Dict[str, Any]:
        """Parse receipt from text directly (for testing)"""
        return self._parse_text(text)
