"""
Chunking service for the LLM Training Platform.
"""

import re
from typing import List, Dict, Any, Optional, Union, Tuple
from loguru import logger

from src.data_structuring.api.schemas import ChunkStrategy


class ChunkingService:
    """Service for chunking document text."""
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE,
    ) -> List[str]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in tokens/characters
            chunk_overlap: Overlap between chunks in tokens/characters
            strategy: Chunking strategy
            
        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []
        
        # Select chunking strategy
        if strategy == ChunkStrategy.FIXED_SIZE:
            return self._chunk_by_fixed_size(text, chunk_size, chunk_overlap)
        elif strategy == ChunkStrategy.SENTENCE:
            return self._chunk_by_sentence(text, chunk_size, chunk_overlap)
        elif strategy == ChunkStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, chunk_size, chunk_overlap)
        elif strategy == ChunkStrategy.SEMANTIC:
            return self._chunk_by_semantic(text, chunk_size, chunk_overlap)
        else:
            # Default to fixed size
            return self._chunk_by_fixed_size(text, chunk_size, chunk_overlap)
    
    def _chunk_by_fixed_size(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Chunk text by fixed size.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            List[str]: List of text chunks
        """
        chunks = []
        
        # Calculate step size
        step_size = chunk_size - chunk_overlap
        
        # Check if step size is valid
        if step_size <= 0:
            logger.warning(f"Invalid step size: {step_size}. Using chunk_size as step size.")
            step_size = chunk_size
        
        # Split text into chunks
        for i in range(0, len(text), step_size):
            # Get chunk
            chunk = text[i:i + chunk_size]
            
            # Add chunk if not empty
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_sentence(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Chunk text by sentence.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            List[str]: List of text chunks
        """
        # Split text into sentences
        sentences = self._split_into_sentences(text)
        
        # Combine sentences into chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding the sentence would exceed chunk size, add current chunk to chunks
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                
                # Start new chunk with overlap
                if chunk_overlap > 0:
                    # Find the last few sentences that fit within the overlap
                    overlap_text = current_chunk[-chunk_overlap:]
                    # Find the last sentence boundary within the overlap
                    sentence_boundaries = list(re.finditer(r'[.!?]\s+', overlap_text))
                    if sentence_boundaries:
                        last_boundary = sentence_boundaries[-1].end()
                        current_chunk = current_chunk[-chunk_overlap + last_boundary:]
                    else:
                        # If no sentence boundary found, use the last few words
                        words = overlap_text.split()
                        if words:
                            current_chunk = " ".join(words[-min(5, len(words)):])
                        else:
                            current_chunk = ""
                else:
                    current_chunk = ""
            
            # Add sentence to current chunk
            if current_chunk and not current_chunk.endswith(" "):
                current_chunk += " "
            current_chunk += sentence
        
        # Add the last chunk if not empty
        if current_chunk.strip():
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_paragraph(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Chunk text by paragraph.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            List[str]: List of text chunks
        """
        # Split text into paragraphs
        paragraphs = self._split_into_paragraphs(text)
        
        # Combine paragraphs into chunks
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding the paragraph would exceed chunk size, add current chunk to chunks
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                
                # Start new chunk with overlap
                if chunk_overlap > 0:
                    # Find the last paragraph that fits within the overlap
                    overlap_text = current_chunk[-chunk_overlap:]
                    # Find the last paragraph boundary within the overlap
                    paragraph_boundaries = list(re.finditer(r'\n\s*\n', overlap_text))
                    if paragraph_boundaries:
                        last_boundary = paragraph_boundaries[-1].end()
                        current_chunk = current_chunk[-chunk_overlap + last_boundary:]
                    else:
                        # If no paragraph boundary found, use the last sentence
                        sentences = self._split_into_sentences(overlap_text)
                        if sentences:
                            current_chunk = sentences[-1]
                        else:
                            current_chunk = ""
                else:
                    current_chunk = ""
            
            # Add paragraph to current chunk
            if current_chunk and not current_chunk.endswith("\n\n"):
                current_chunk += "\n\n"
            current_chunk += paragraph
        
        # Add the last chunk if not empty
        if current_chunk.strip():
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_semantic(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Chunk text by semantic units (experimental).
        
        This is a placeholder for a more sophisticated semantic chunking algorithm.
        Currently, it falls back to sentence-based chunking.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            List[str]: List of text chunks
        """
        # For now, fall back to sentence-based chunking
        logger.info("Semantic chunking not fully implemented, falling back to sentence-based chunking.")
        return self._chunk_by_sentence(text, chunk_size, chunk_overlap)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: List of sentences
        """
        # Simple sentence splitting
        # This is a basic implementation and may not handle all cases correctly
        # For production use, consider using a more sophisticated sentence tokenizer
        
        # Handle common abbreviations to avoid splitting at them
        text = re.sub(r'(Mr\.|Mrs\.|Dr\.|Prof\.|etc\.)', r'\1<POINT>', text)
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
        
        # Restore abbreviations
        sentences = [re.sub(r'<POINT>', '.', s) for s in sentences]
        
        # Filter out empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        return sentences
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: List of paragraphs
        """
        # Split on paragraph boundaries (one or more newlines)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out empty paragraphs
        paragraphs = [p for p in paragraphs if p.strip()]
        
        return paragraphs


class ArabicChunkingService(ChunkingService):
    """Service for chunking Arabic document text."""
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split Arabic text into sentences.
        
        Args:
            text: Arabic text to split
            
        Returns:
            List[str]: List of sentences
        """
        # Arabic-specific sentence splitting
        # Arabic sentences typically end with a period (.), question mark (؟), or exclamation mark (!)
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=\.|\?|!|؟|!) ', text)
        
        # Filter out empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        return sentences
