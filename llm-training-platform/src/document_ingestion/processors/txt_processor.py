"""
TXT Processor module for handling plain text files
"""

import os
import chardet
from pathlib import Path
from typing import Union, Optional, Dict
from loguru import logger


class TxtProcessor:
    """
    Class for processing TXT documents
    """
    
    def extract_text(self, txt_path: Union[str, Path]) -> str:
        """
        Extract text from a TXT file with encoding detection
        
        Args:
            txt_path: Path to the TXT file
            
        Returns:
            str: Extracted text
        """
        try:
            # Read the file in binary mode to detect encoding
            with open(str(txt_path), 'rb') as file:
                raw_data = file.read()
            
            # Detect encoding
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
            confidence = result['confidence']
            
            logger.info(f"Detected encoding: {encoding} with confidence: {confidence}")
            
            # Read the file with the detected encoding
            try:
                with open(str(txt_path), 'r', encoding=encoding) as file:
                    text = file.read()
            except UnicodeDecodeError:
                # Fall back to utf-8 if the detected encoding fails
                logger.warning(f"Failed to decode with {encoding}, falling back to utf-8")
                with open(str(txt_path), 'r', encoding='utf-8', errors='replace') as file:
                    text = file.read()
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the text
        
        Args:
            text: Input text
            
        Returns:
            str: Detected language code
        """
        try:
            from langdetect import detect
            
            # Get a sample of the text for language detection
            sample = text[:min(5000, len(text))]
            
            # Detect language
            lang = detect(sample)
            
            return lang
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return "unknown"
    
    def get_metadata(self, txt_path: Union[str, Path]) -> Dict[str, str]:
        """
        Get metadata for a TXT file
        
        Args:
            txt_path: Path to the TXT file
            
        Returns:
            Dict[str, str]: File metadata
        """
        try:
            # Get file stats
            stats = os.stat(str(txt_path))
            
            # Extract text for language detection
            text = self.extract_text(txt_path)
            
            # Detect language
            language = self.detect_language(text)
            
            # Create metadata dictionary
            metadata = {
                "filename": os.path.basename(txt_path),
                "size_bytes": str(stats.st_size),
                "created": str(stats.st_ctime),
                "modified": str(stats.st_mtime),
                "language": language,
                "line_count": str(text.count('\n') + 1),
                "word_count": str(len(text.split())),
                "char_count": str(len(text)),
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting TXT metadata: {str(e)}")
            return {
                "filename": os.path.basename(txt_path),
                "error": str(e)
            }
    
    def split_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
        """
        Split text into overlapping chunks
        
        Args:
            text: Input text
            chunk_size: Size of each chunk in words
            overlap: Number of overlapping words between chunks
            
        Returns:
            list: List of text chunks
        """
        try:
            words = text.split()
            chunks = []
            
            # If text is smaller than chunk size, return as is
            if len(words) <= chunk_size:
                return [text]
            
            # Split into overlapping chunks
            for i in range(0, len(words), chunk_size - overlap):
                chunk = words[i:i + chunk_size]
                chunks.append(" ".join(chunk))
                
                # Break if we've reached the end
                if i + chunk_size >= len(words):
                    break
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting text into chunks: {str(e)}")
            return [text]
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract sections from text based on headings
        
        Args:
            text: Input text
            
        Returns:
            Dict[str, str]: Dictionary mapping section headings to content
        """
        try:
            lines = text.split('\n')
            sections = {}
            current_section = "DEFAULT"
            current_content = []
            
            # Simple heuristic for section detection
            for line in lines:
                stripped = line.strip()
                
                # Check if line is a potential heading
                if (
                    stripped and 
                    len(stripped) < 100 and  # Not too long
                    stripped.upper() == stripped and  # All uppercase
                    not stripped.endswith('.') and  # Doesn't end with period
                    not stripped.startswith('•') and  # Not a bullet point
                    not stripped.startswith('-')  # Not a list item
                ):
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = stripped
                    current_content = []
                else:
                    current_content.append(line)
            
            # Save the last section
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {str(e)}")
            return {"DEFAULT": text}
