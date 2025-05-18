"""
Image Preprocessor module for enhancing images before OCR
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple
from loguru import logger


class ImagePreprocessor:
    """
    Class for preprocessing images to improve OCR results
    """
    
    def preprocess(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Apply a series of preprocessing steps to improve OCR accuracy
        
        Args:
            image_path: Path to the image file
            
        Returns:
            np.ndarray: Preprocessed image
        """
        try:
            # Read the image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to read image: {image_path}")
                return None
            
            # Apply preprocessing steps
            image = self.resize_if_needed(image)
            image = self.deskew(image)
            image = self.remove_noise(image)
            image = self.normalize(image)
            image = self.binarize(image)
            
            return image
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {str(e)}")
            return None
    
    def resize_if_needed(self, image: np.ndarray, min_width: int = 1000) -> np.ndarray:
        """
        Resize the image if it's too small
        
        Args:
            image: Input image
            min_width: Minimum width for good OCR results
            
        Returns:
            np.ndarray: Resized image if needed, original otherwise
        """
        try:
            height, width = image.shape[:2]
            
            # If image is already large enough, return as is
            if width >= min_width:
                return image
            
            # Calculate new dimensions while maintaining aspect ratio
            new_width = min_width
            new_height = int(height * (new_width / width))
            
            # Resize image
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            return resized
            
        except Exception as e:
            logger.error(f"Image resize error: {str(e)}")
            return image
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew the image to straighten text
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Deskewed image
        """
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Threshold the image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find all contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find largest contour
            largest_contour = max(contours, key=cv2.contourArea, default=None)
            
            if largest_contour is None:
                return image
            
            # Get minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            
            # Adjust angle
            if angle < -45:
                angle = 90 + angle
            
            # Rotate the image to deskew
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            return rotated
            
        except Exception as e:
            logger.error(f"Image deskew error: {str(e)}")
            return image
    
    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from the image
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Denoised image
        """
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply bilateral filter to remove noise while preserving edges
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            
            return denoised
            
        except Exception as e:
            logger.error(f"Image noise removal error: {str(e)}")
            return image
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize the image to improve contrast
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Normalized image
        """
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            normalized = clahe.apply(gray)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Image normalization error: {str(e)}")
            return image
    
    def binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Binarize the image to improve OCR
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Binarized image
        """
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            return binary
            
        except Exception as e:
            logger.error(f"Image binarization error: {str(e)}")
            return image
    
    def enhance_text(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance text in the image
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Image with enhanced text
        """
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Create a kernel for morphological operations
            kernel = np.ones((1, 1), np.uint8)
            
            # Apply morphological operations to enhance text
            img_erosion = cv2.erode(gray, kernel, iterations=1)
            img_dilation = cv2.dilate(img_erosion, kernel, iterations=1)
            
            return img_dilation
            
        except Exception as e:
            logger.error(f"Text enhancement error: {str(e)}")
            return image
    
    def remove_borders(self, image: np.ndarray) -> np.ndarray:
        """
        Remove borders from the image
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Image with borders removed
        """
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Threshold the image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find the largest contour (assuming it's the content)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Crop the image to remove borders
                cropped = gray[y:y+h, x:x+w]
                return cropped
            
            return gray
            
        except Exception as e:
            logger.error(f"Border removal error: {str(e)}")
            return image
