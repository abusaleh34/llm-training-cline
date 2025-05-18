"""
PDF Processor module for handling PDF documents
"""

import os
import fitz  # PyMuPDF
import tempfile
from pathlib import Path
from typing import List, Optional
from pdf2image import convert_from_path
from loguru import logger


class PDFProcessor:
    """
    Class for processing PDF documents
    """
    
    def is_searchable(self, pdf_path: Path) -> bool:
        """
        Check if a PDF is searchable (contains text) or is a scanned image
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: True if the PDF is searchable, False if it's a scanned image
        """
        try:
            # Open the PDF
            pdf_document = fitz.open(str(pdf_path))
            
            # Check if the PDF has text
            has_text = False
            
            # Check first few pages (up to 5) for text
            for page_num in range(min(5, pdf_document.page_count)):
                page = pdf_document[page_num]
                text = page.get_text()
                
                # If we find a reasonable amount of text, consider it searchable
                if len(text.strip()) > 50:  # Arbitrary threshold
                    has_text = True
                    break
            
            pdf_document.close()
            return has_text
            
        except Exception as e:
            logger.error(f"Error checking if PDF is searchable: {str(e)}")
            # Default to assuming it's not searchable if there's an error
            return False
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from a searchable PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text
        """
        try:
            # Open the PDF
            pdf_document = fitz.open(str(pdf_path))
            
            # Extract text from all pages
            text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text()
                text += "\n\n"  # Add separation between pages
            
            pdf_document.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def convert_to_images(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        Convert a PDF to a list of images (one per page)
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the images
            
        Returns:
            List[Path]: List of paths to the generated images
        """
        try:
            # Convert PDF to images
            images = convert_from_path(
                str(pdf_path),
                dpi=300,  # Higher DPI for better OCR results
                output_folder=str(output_dir),
                fmt="png",
                thread_count=os.cpu_count() or 1
            )
            
            # Get paths to the generated images
            image_paths = []
            for i, _ in enumerate(images):
                image_path = output_dir / f"page_{i+1}.png"
                image_paths.append(image_path)
            
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise
    
    def get_metadata(self, pdf_path: Path) -> dict:
        """
        Extract metadata from a PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            dict: PDF metadata
        """
        try:
            # Open the PDF
            pdf_document = fitz.open(str(pdf_path))
            
            # Extract metadata
            metadata = pdf_document.metadata
            
            # Add page count
            metadata["page_count"] = pdf_document.page_count
            
            pdf_document.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF: {str(e)}")
            return {}
    
    def extract_images(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        Extract embedded images from a PDF
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the images
            
        Returns:
            List[Path]: List of paths to the extracted images
        """
        try:
            # Open the PDF
            pdf_document = fitz.open(str(pdf_path))
            
            image_paths = []
            image_count = 0
            
            # Iterate through pages
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Get images
                image_list = page.get_images(full=True)
                
                # Extract images
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Determine image extension
                    image_ext = base_image["ext"]
                    
                    # Save image
                    image_path = output_dir / f"image_{page_num+1}_{img_index+1}.{image_ext}"
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    image_paths.append(image_path)
                    image_count += 1
            
            pdf_document.close()
            logger.info(f"Extracted {image_count} images from PDF")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {str(e)}")
            return []
