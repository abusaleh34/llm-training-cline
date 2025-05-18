"""
File encryption utilities for document ingestion.

This module provides functions for encrypting and decrypting document files.
"""

import os
from pathlib import Path
from typing import Union, Optional

from src.security import encryption_manager
from src.common.config.settings import settings
from loguru import logger


def encrypt_document(file_path: Union[str, Path]) -> Path:
    """
    Encrypt a document file.
    
    Args:
        file_path: Path to the document file to encrypt.
        
    Returns:
        Path: Path to the encrypted document file.
    """
    try:
        file_path = Path(file_path)
        encrypted_path = encryption_manager.encrypt_file(file_path)
        logger.info(f"Document encrypted: {file_path} -> {encrypted_path}")
        return encrypted_path
    except Exception as e:
        logger.error(f"Failed to encrypt document {file_path}: {str(e)}")
        raise


def decrypt_document(file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Decrypt a document file.
    
    Args:
        file_path: Path to the encrypted document file.
        output_path: Path to save the decrypted document file. If not provided, the decrypted file
                     will be saved with the same name as the input file without '.enc' extension.
        
    Returns:
        Path: Path to the decrypted document file.
    """
    try:
        file_path = Path(file_path)
        decrypted_path = encryption_manager.decrypt_file(file_path, output_path)
        logger.info(f"Document decrypted: {file_path} -> {decrypted_path}")
        return decrypted_path
    except Exception as e:
        logger.error(f"Failed to decrypt document {file_path}: {str(e)}")
        raise


def encrypt_documents_in_directory(directory: Union[str, Path]) -> int:
    """
    Encrypt all documents in a directory.
    
    Args:
        directory: Path to the directory containing documents to encrypt.
        
    Returns:
        int: Number of documents encrypted.
    """
    directory = Path(directory)
    count = 0
    
    for file_path in directory.glob("**/*"):
        if file_path.is_file() and not file_path.name.endswith(".enc"):
            try:
                encrypt_document(file_path)
                count += 1
            except Exception as e:
                logger.error(f"Failed to encrypt {file_path}: {str(e)}")
    
    logger.info(f"Encrypted {count} documents in {directory}")
    return count


def decrypt_documents_in_directory(directory: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> int:
    """
    Decrypt all encrypted documents in a directory.
    
    Args:
        directory: Path to the directory containing encrypted documents.
        output_dir: Directory to save decrypted documents. If not provided, decrypted files
                    will be saved in the same directory as the encrypted files.
        
    Returns:
        int: Number of documents decrypted.
    """
    directory = Path(directory)
    count = 0
    
    for file_path in directory.glob("**/*.enc"):
        if file_path.is_file():
            try:
                if output_dir:
                    # Create relative path structure in output directory
                    rel_path = file_path.relative_to(directory)
                    output_path = Path(output_dir) / rel_path.with_suffix("")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    decrypt_document(file_path, output_path)
                else:
                    decrypt_document(file_path)
                count += 1
            except Exception as e:
                logger.error(f"Failed to decrypt {file_path}: {str(e)}")
    
    logger.info(f"Decrypted {count} documents in {directory}")
    return count
