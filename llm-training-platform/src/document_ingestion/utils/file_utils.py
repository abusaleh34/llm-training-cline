"""
File utility functions for document ingestion service
"""

import os
import mimetypes
import magic
from pathlib import Path
from loguru import logger


def create_directory_if_not_exists(directory_path: Path) -> None:
    """
    Create a directory if it doesn't exist
    
    Args:
        directory_path: Path to the directory
    """
    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory_path}")


def get_file_type(file_path: Path) -> str:
    """
    Determine the file type based on content analysis
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: File type (pdf, docx, txt, etc.)
    """
    # Initialize mimetypes
    mimetypes.init()
    
    # Try to determine file type using python-magic
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))
        
        if mime_type == "application/pdf":
            return "pdf"
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "docx"
        elif mime_type == "text/plain":
            return "txt"
        
        # Fall back to extension-based detection if mime type is not recognized
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == ".pdf":
            return "pdf"
        elif file_extension == ".docx":
            return "docx"
        elif file_extension == ".txt":
            return "txt"
        else:
            logger.warning(f"Unrecognized file type for {file_path}. Mime type: {mime_type}, Extension: {file_extension}")
            raise ValueError(f"Unsupported file type: {file_extension}")
            
    except Exception as e:
        logger.error(f"Error determining file type: {str(e)}")
        
        # Fall back to extension-based detection
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == ".pdf":
            return "pdf"
        elif file_extension == ".docx":
            return "docx"
        elif file_extension == ".txt":
            return "txt"
        else:
            logger.error(f"Unsupported file extension: {file_extension}")
            raise ValueError(f"Unsupported file type: {file_extension}")


def is_valid_file_type(file_path: Path) -> bool:
    """
    Check if the file type is supported
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if the file type is supported, False otherwise
    """
    try:
        file_type = get_file_type(file_path)
        return file_type in ["pdf", "docx", "txt"]
    except ValueError:
        return False


def get_file_size(file_path: Path) -> int:
    """
    Get the size of a file in bytes
    
    Args:
        file_path: Path to the file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(file_path)


def get_file_extension(filename: str) -> str:
    """
    Get the extension of a file
    
    Args:
        filename: Name of the file
        
    Returns:
        str: File extension
    """
    return os.path.splitext(filename)[1].lower()
