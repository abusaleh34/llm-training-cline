"""
OCR Engine module for extracting text from images
"""

import os
import cv2
import pytesseract
import numpy as np
from pathlib import Path
from typing import Union, Optional
from loguru import logger
import arabic_reshaper
from bidi.algorithm import get_display


class OCREngine:
    """
    Class for OCR processing with special handling for Arabic text
    """
    
    def __init__(self):
        """
        Initialize OCR Engine
        """
        # Set Tesseract path if needed (uncomment and modify if Tesseract is not in PATH)
        # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        
        # Configure Tesseract parameters
        self.config = {
            'ar': '--psm 3 --oem 1 -l ara',  # Arabic
            'en': '--psm 3 --oem 1 -l eng',  # English
            'ar+en': '--psm 3 --oem 1 -l ara+eng',  # Arabic + English
        }
    
    def process_image(self, image_path: Union[str, Path], language: str = 'ar') -> str:
        """
        Process an image and extract text using OCR
        
        Args:
            image_path: Path to the image file
            language: Language code ('ar' for Arabic, 'en' for English, 'ar+en' for both)
            
        Returns:
            str: Extracted text
        """
        try:
            # Read the image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to read image: {image_path}")
                return ""
            
            # Get OCR configuration based on language
            config = self.config.get(language, self.config['ar'])
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=config)
            
            # Handle Arabic text if needed
            if language in ['ar', 'ar+en']:
                text = self._process_arabic_text(text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            return ""
    
    def process_image_regions(self, image_path: Union[str, Path], regions: list, language: str = 'ar') -> dict:
        """
        Process specific regions of an image and extract text
        
        Args:
            image_path: Path to the image file
            regions: List of regions as (x, y, width, height)
            language: Language code
            
        Returns:
            dict: Dictionary mapping region indices to extracted text
        """
        try:
            # Read the image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to read image: {image_path}")
                return {}
            
            # Get OCR configuration based on language
            config = self.config.get(language, self.config['ar'])
            
            results = {}
            
            # Process each region
            for i, (x, y, w, h) in enumerate(regions):
                # Extract region
                roi = image[y:y+h, x:x+w]
                
                # Perform OCR on region
                text = pytesseract.image_to_string(roi, config=config)
                
                # Handle Arabic text if needed
                if language in ['ar', 'ar+en']:
                    text = self._process_arabic_text(text)
                
                results[i] = text.strip()
            
            return results
            
        except Exception as e:
            logger.error(f"OCR region processing error: {str(e)}")
            return {}
    
    def _process_arabic_text(self, text: str) -> str:
        """
        Process Arabic text for correct display
        
        Args:
            text: Raw Arabic text from OCR
            
        Returns:
            str: Processed Arabic text
        """
        try:
            # Reshape Arabic text
            reshaped_text = arabic_reshaper.reshape(text)
            
            # Handle bidirectional text
            bidi_text = get_display(reshaped_text)
            
            return bidi_text
            
        except Exception as e:
            logger.warning(f"Error processing Arabic text: {str(e)}")
            return text
    
    def enhance_image_for_ocr(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Enhance an image to improve OCR results
        
        Args:
            image_path: Path to the image file
            
        Returns:
            np.ndarray: Enhanced image
        """
        try:
            # Read the image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to read image: {image_path}")
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
            
            return denoised
            
        except Exception as e:
            logger.error(f"Image enhancement error: {str(e)}")
            return None
    
    def detect_text_regions(self, image_path: Union[str, Path]) -> list:
        """
        Detect regions containing text in an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            list: List of regions as (x, y, width, height)
        """
        try:
            # Read the image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to read image: {image_path}")
                return []
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours to find text regions
            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter out very small regions
                if w > 20 and h > 20:
                    text_regions.append((x, y, w, h))
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Text region detection error: {str(e)}")
            return []
