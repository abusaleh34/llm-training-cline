"""
Document processor factory for selecting the appropriate processor based on file type
"""

from pathlib import Path
from typing import Union, Optional
from loguru import logger

from src.document_ingestion.utils.file_utils import get_file_type
from src.document_ingestion.processors.pdf_processor import PDFProcessor
from src.document_ingestion.processors.docx_processor import DocxProcessor
from src.document_ingestion.processors.txt_processor import TxtProcessor


class ProcessorFactory:
    """
    Factory class for creating document processors based on file type
    """
    
    @staticmethod
    def get_processor(file_path: Union[str, Path]):
        """
        Get the appropriate processor for a file based on its type
        
        Args:
            file_path: Path to the file
            
        Returns:
            Document processor instance
            
        Raises:
            ValueError: If the file type is not supported
        """
        try:
            # Get the file type
            file_type = get_file_type(Path(file_path))
            
            # Create the appropriate processor
            if file_type == "pdf":
                logger.info(f"Creating PDF processor for {file_path}")
                return PDFProcessor()
            elif file_type == "docx":
                logger.info(f"Creating DOCX processor for {file_path}")
                return DocxProcessor()
            elif file_type == "txt":
                logger.info(f"Creating TXT processor for {file_path}")
                return TxtProcessor()
            else:
                logger.error(f"Unsupported file type: {file_type}")
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error creating processor: {str(e)}")
            raise


class DocumentProcessor:
    """
    Main document processor that delegates to specific processors
    """
    
    def __init__(self):
        """
        Initialize the document processor
        """
        self.factory = ProcessorFactory()
    
    def process_document(self, file_path: Union[str, Path], output_dir: Optional[Path] = None) -> dict:
        """
        Process a document
        
        Args:
            file_path: Path to the document
            output_dir: Directory to save processed files (optional)
            
        Returns:
            dict: Processing results
        """
        try:
            # Convert to Path object
            file_path = Path(file_path)
            
            # Create output directory if provided
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Get the appropriate processor
            processor = self.factory.get_processor(file_path)
            
            # Process based on file type
            file_type = get_file_type(file_path)
            
            result = {
                "file_path": str(file_path),
                "file_type": file_type,
                "success": False,
                "text": "",
                "metadata": {},
                "error": None
            }
            
            # Extract text
            try:
                if file_type == "pdf":
                    # Check if PDF is searchable
                    is_searchable = processor.is_searchable(file_path)
                    result["is_searchable"] = is_searchable
                    
                    # Extract text
                    if is_searchable:
                        result["text"] = processor.extract_text(file_path)
                    else:
                        # For non-searchable PDFs, convert to images and use OCR
                        # This would be handled by the OCR module
                        result["requires_ocr"] = True
                        
                        # If output directory is provided, convert to images
                        if output_dir:
                            result["images"] = processor.convert_to_images(file_path, output_dir)
                    
                    # Get metadata
                    result["metadata"] = processor.get_metadata(file_path)
                    
                    # Extract images if output directory is provided
                    if output_dir:
                        result["extracted_images"] = processor.extract_images(file_path, output_dir)
                    
                elif file_type == "docx":
                    # Extract text
                    result["text"] = processor.extract_text(file_path)
                    
                    # Get metadata
                    result["metadata"] = processor.extract_metadata(file_path)
                    
                    # Extract headers and footers
                    result["headers_footers"] = processor.extract_headers_footers(file_path)
                    
                    # Extract document structure
                    result["structure"] = processor.extract_structure(file_path)
                    
                    # Extract images if output directory is provided
                    if output_dir:
                        result["extracted_images"] = processor.extract_images(file_path, output_dir)
                    
                elif file_type == "txt":
                    # Extract text
                    result["text"] = processor.extract_text(file_path)
                    
                    # Get metadata
                    result["metadata"] = processor.get_metadata(file_path)
                    
                    # Extract sections
                    result["sections"] = processor.extract_sections(result["text"])
                
                # Mark as successful
                result["success"] = True
                
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                result["error"] = str(e)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in document processing: {str(e)}")
            return {
                "file_path": str(file_path),
                "success": False,
                "error": str(e)
            }
