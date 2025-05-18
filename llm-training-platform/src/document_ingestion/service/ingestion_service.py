"""
Document ingestion service for handling document uploads and processing
"""

import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from loguru import logger
import cv2

from sqlalchemy.orm import Session

from src.common.config.settings import settings
from src.common.models.document import Document, DocumentStatus
from src.document_ingestion.utils.file_utils import create_directory_if_not_exists, is_valid_file_type
from src.document_ingestion.utils.file_encryption import encrypt_document, decrypt_document
from src.document_ingestion.processors.processor_factory import DocumentProcessor
from src.document_ingestion.ocr.ocr_engine import OCREngine
from src.document_ingestion.preprocessing.image_preprocessor import ImagePreprocessor
from src.document_ingestion.preprocessing.text_preprocessor import TextPreprocessor


class IngestionService:
    """
    Service for handling document ingestion
    """
    
    def __init__(self, db: Session):
        """
        Initialize the ingestion service
        
        Args:
            db: Database session
        """
        self.db = db
        self.document_processor = DocumentProcessor()
        self.ocr_engine = OCREngine()
        self.image_preprocessor = ImagePreprocessor()
        self.text_preprocessor = TextPreprocessor()
        
        # Create necessary directories
        create_directory_if_not_exists(Path(settings.document.upload_dir))
        create_directory_if_not_exists(Path(settings.document.processed_dir))
        create_directory_if_not_exists(Path(settings.document.temp_dir))
    
    def upload_document(self, file_path: Union[str, Path], filename: str, user_id: str, 
                        language: str = "ar", document_type: Optional[str] = None) -> Document:
        """
        Upload a document
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            user_id: ID of the user uploading the document
            language: Document language
            document_type: Type of document (contract, letter, etc.)
            
        Returns:
            Document: Created document record
            
        Raises:
            ValueError: If the file type is not supported
        """
        try:
            # Convert to Path object
            file_path = Path(file_path)
            
            # Check if file type is supported
            if not is_valid_file_type(file_path):
                raise ValueError(f"Unsupported file type: {file_path}")
            
            # Generate a unique ID for the document
            document_id = str(uuid.uuid4())
            
            # Create a directory for the document
            document_dir = Path(settings.document.upload_dir) / document_id
            create_directory_if_not_exists(document_dir)
            
            # Copy the file to the document directory
            dest_path = document_dir / filename
            shutil.copy2(file_path, dest_path)
            
            # Encrypt the document if encryption is enabled
            if settings.security.encryption_master_key:
                try:
                    encrypted_path = encrypt_document(dest_path)
                    logger.info(f"Document encrypted: {dest_path} -> {encrypted_path}")
                    # Update the path to the encrypted file
                    dest_path = encrypted_path
                except Exception as e:
                    logger.error(f"Failed to encrypt document: {str(e)}")
            
            # Create document record
            document = Document(
                id=document_id,
                filename=filename,
                file_path=str(dest_path),
                file_type=os.path.splitext(filename)[1].lower()[1:],  # Remove the dot
                document_type=document_type,
                language=language,
                status=DocumentStatus.UPLOADED,
                user_id=user_id,
                upload_date=datetime.now()
            )
            
            # Save to database
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Document uploaded: {document.id} - {document.filename}")
            
            return document
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise
    
    def process_document(self, document_id: str) -> Dict[str, Any]:
        """
        Process a document
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Dict[str, Any]: Processing results
            
        Raises:
            ValueError: If the document is not found
        """
        try:
            # Get the document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                raise ValueError(f"Document not found: {document_id}")
            
            # Update document status
            document.status = DocumentStatus.PROCESSING
            document.processing_started_date = datetime.now()
            self.db.commit()
            
            logger.info(f"Processing document: {document.id} - {document.filename}")
            
            # Create output directory for processed files
            output_dir = Path(settings.document.processed_dir) / document_id
            create_directory_if_not_exists(output_dir)
            
            # Decrypt the document if it's encrypted
            file_path = document.file_path
            temp_decrypted_path = None
            
            if settings.security.encryption_master_key and document.file_path.endswith('.enc'):
                try:
                    temp_dir = Path(settings.document.temp_dir) / document.id
                    create_directory_if_not_exists(temp_dir)
                    temp_decrypted_path = decrypt_document(document.file_path, temp_dir / Path(document.file_path).stem)
                    file_path = str(temp_decrypted_path)
                    logger.info(f"Document decrypted for processing: {document.file_path} -> {file_path}")
                except Exception as e:
                    logger.error(f"Failed to decrypt document for processing: {str(e)}")
            
            # Process the document
            result = self.document_processor.process_document(file_path, output_dir)
            
            # Handle OCR if needed
            if result.get("requires_ocr", False):
                logger.info(f"Document requires OCR: {document.id}")
                ocr_result = self._process_ocr(document, result, output_dir)
                result.update(ocr_result)
            
            # Preprocess text
            if result.get("text"):
                result["text"] = self.text_preprocessor.preprocess(
                    result["text"], 
                    language=document.language
                )
            
            # Clean up temporary decrypted file
            if temp_decrypted_path and os.path.exists(temp_decrypted_path):
                try:
                    os.remove(temp_decrypted_path)
                    logger.info(f"Temporary decrypted file removed: {temp_decrypted_path}")
                except Exception as e:
                    logger.error(f"Failed to remove temporary decrypted file: {str(e)}")
            
            # Encrypt processed files if encryption is enabled
            if settings.security.encryption_master_key:
                try:
                    # Encrypt the extracted text file
                    text_file = output_dir / "extracted_text.txt"
                    if os.path.exists(text_file):
                        encrypt_document(text_file)
                        logger.info(f"Processed text file encrypted: {text_file}")
                    
                    # Encrypt other processed files as needed
                    # ...
                except Exception as e:
                    logger.error(f"Failed to encrypt processed files: {str(e)}")
            
            # Update document record
            document.processed_file_path = str(output_dir)
            
            # Update metadata
            if "metadata" in result:
                if "page_count" in result["metadata"]:
                    document.page_count = result["metadata"]["page_count"]
                
                # Count words in the extracted text
                if result.get("text"):
                    document.word_count = len(result["text"].split())
            
            # Update status
            if result["success"]:
                document.status = DocumentStatus.PROCESSED
                document.processing_completed_date = datetime.now()
            else:
                document.status = DocumentStatus.ERROR
                document.error_message = result.get("error", "Unknown error")
            
            self.db.commit()
            
            logger.info(f"Document processed: {document.id} - Status: {document.status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            
            # Update document status
            try:
                document = self.db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.status = DocumentStatus.ERROR
                    document.error_message = str(e)
                    self.db.commit()
            except Exception as db_error:
                logger.error(f"Error updating document status: {str(db_error)}")
            
            raise
    
    def _process_ocr(self, document: Document, process_result: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        """
        Process OCR for a document
        
        Args:
            document: Document record
            process_result: Results from document processing
            output_dir: Directory to save processed files
            
        Returns:
            Dict[str, Any]: OCR results
        """
        try:
            logger.info(f"Starting OCR processing for document: {document.id}")
            
            ocr_result = {
                "ocr_processed": True,
                "text": ""
            }
            
            # Get images from the process result
            images = process_result.get("images", [])
            
            if not images:
                logger.warning(f"No images found for OCR processing: {document.id}")
                return ocr_result
            
            # Create OCR output directory
            ocr_dir = output_dir / "ocr"
            create_directory_if_not_exists(ocr_dir)
            
            # Process each image
            all_text = []
            
            for i, image_path in enumerate(images):
                logger.info(f"Processing OCR for image {i+1}/{len(images)}: {image_path}")
                
                # Preprocess the image
                enhanced_image = self.image_preprocessor.preprocess(image_path)
                
                # Save enhanced image
                enhanced_path = ocr_dir / f"enhanced_{i+1}.png"
                cv2.imwrite(str(enhanced_path), enhanced_image)
                
                # Perform OCR
                text = self.ocr_engine.process_image(enhanced_path, language=document.language)
                
                # Add to results
                all_text.append(text)
            
            # Combine all text
            combined_text = "\n\n".join(all_text)
            
            # Preprocess the text
            processed_text = self.text_preprocessor.preprocess(combined_text, language=document.language)
            
            ocr_result["text"] = processed_text
            
            # Save the extracted text
            text_path = output_dir / "extracted_text.txt"
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(processed_text)
            
            logger.info(f"OCR processing completed for document: {document.id}")
            
            return ocr_result
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            return {
                "ocr_processed": False,
                "ocr_error": str(e)
            }
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents_by_user(self, user_id: str) -> List[Document]:
        """
        Get all documents for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List[Document]: List of documents
        """
        return self.db.query(Document).filter(Document.user_id == user_id).all()
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document
        
        Args:
            document_id: Document ID
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            # Get the document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return False
            
            # Delete the document files
            if document.file_path and os.path.exists(document.file_path):
                os.remove(document.file_path)
                # Also remove the non-encrypted version if it exists
                if document.file_path.endswith('.enc'):
                    non_encrypted_path = document.file_path[:-4]  # Remove .enc extension
                    if os.path.exists(non_encrypted_path):
                        os.remove(non_encrypted_path)
            
            # Delete the processed files
            if document.processed_file_path and os.path.exists(document.processed_file_path):
                shutil.rmtree(document.processed_file_path)
            
            # Delete the document record
            self.db.delete(document)
            self.db.commit()
            
            logger.info(f"Document deleted: {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
