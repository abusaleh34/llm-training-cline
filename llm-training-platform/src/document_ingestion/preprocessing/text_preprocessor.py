"""
Text Preprocessor module for cleaning and normalizing extracted text
"""

import re
import string
import unicodedata
from typing import List, Optional
from loguru import logger

import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import pyarabic.araby as araby
from camel_tools.utils.normalize import normalize_unicode, normalize_alef, normalize_alef_maksura
from camel_tools.utils.dediac import dediac_ar


class TextPreprocessor:
    """
    Class for preprocessing text, with special handling for Arabic text
    """
    
    def __init__(self):
        """
        Initialize Text Preprocessor
        """
        # Download NLTK resources if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
    
    def preprocess(self, text: str, language: str = 'ar') -> str:
        """
        Apply a series of preprocessing steps to clean and normalize text
        
        Args:
            text: Input text
            language: Language code ('ar' for Arabic, 'en' for English)
            
        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""
        
        try:
            # Remove OCR artifacts
            text = self.remove_ocr_artifacts(text)
            
            # Handle language-specific preprocessing
            if language == 'ar':
                text = self.preprocess_arabic(text)
            elif language == 'en':
                text = self.preprocess_english(text)
            elif language == 'ar+en':
                # For mixed text, apply both with Arabic first
                text = self.preprocess_arabic(text)
                text = self.preprocess_english(text, preserve_arabic=True)
            
            # General cleaning
            text = self.remove_extra_whitespace(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Text preprocessing error: {str(e)}")
            return text
    
    def preprocess_arabic(self, text: str) -> str:
        """
        Preprocess Arabic text
        
        Args:
            text: Input Arabic text
            
        Returns:
            str: Preprocessed Arabic text
        """
        try:
            # Normalize Unicode
            text = normalize_unicode(text)
            
            # Normalize Alef forms
            text = normalize_alef(text)
            
            # Normalize Alef Maksura
            text = normalize_alef_maksura(text)
            
            # Remove diacritics (optional, may affect meaning)
            # text = dediac_ar(text)
            
            # Remove tatweel (kashida)
            text = araby.strip_tatweel(text)
            
            # Normalize spaces and punctuation
            text = self.normalize_punctuation(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Arabic text preprocessing error: {str(e)}")
            return text
    
    def preprocess_english(self, text: str, preserve_arabic: bool = False) -> str:
        """
        Preprocess English text
        
        Args:
            text: Input English text
            preserve_arabic: Whether to preserve Arabic characters
            
        Returns:
            str: Preprocessed English text
        """
        try:
            # Convert to lowercase (skip if preserving Arabic)
            if not preserve_arabic:
                text = text.lower()
            
            # Normalize Unicode
            text = unicodedata.normalize('NFKC', text)
            
            # Normalize punctuation
            text = self.normalize_punctuation(text)
            
            return text
            
        except Exception as e:
            logger.error(f"English text preprocessing error: {str(e)}")
            return text
    
    def remove_ocr_artifacts(self, text: str) -> str:
        """
        Remove common OCR artifacts
        
        Args:
            text: Input text
            
        Returns:
            str: Text with OCR artifacts removed
        """
        try:
            # Remove non-printable characters
            text = ''.join(c for c in text if c.isprintable() or c.isspace())
            
            # Remove isolated characters that are likely OCR errors
            text = re.sub(r'(?<!\w)[\w](?!\w)', ' ', text)
            
            # Remove repeated punctuation
            text = re.sub(r'([^\w\s])\1+', r'\1', text)
            
            # Fix common OCR errors
            text = text.replace('0', 'o')  # Replace '0' with 'o' when it's likely a letter
            text = text.replace('1', 'l')  # Replace '1' with 'l' when it's likely a letter
            
            return text
            
        except Exception as e:
            logger.error(f"OCR artifact removal error: {str(e)}")
            return text
    
    def normalize_punctuation(self, text: str) -> str:
        """
        Normalize punctuation and spaces
        
        Args:
            text: Input text
            
        Returns:
            str: Text with normalized punctuation
        """
        try:
            # Normalize spaces around punctuation
            text = re.sub(r'\s*([,.!?;:])\s*', r'\1 ', text)
            
            # Normalize quotes
            text = re.sub(r'["""]', '"', text)
            text = re.sub(r"[''']", "'", text)
            
            # Normalize dashes
            text = re.sub(r'[-‐‑‒–—―]', '-', text)
            
            # Fix spacing after periods
            text = re.sub(r'\.(?=[A-Za-z])', '. ', text)
            
            return text
            
        except Exception as e:
            logger.error(f"Punctuation normalization error: {str(e)}")
            return text
    
    def remove_extra_whitespace(self, text: str) -> str:
        """
        Remove extra whitespace
        
        Args:
            text: Input text
            
        Returns:
            str: Text with normalized whitespace
        """
        try:
            # Replace multiple spaces with a single space
            text = re.sub(r'\s+', ' ', text)
            
            # Remove spaces at the beginning and end of each line
            text = re.sub(r'^ +| +$', '', text, flags=re.MULTILINE)
            
            # Normalize line breaks
            text = re.sub(r'\n+', '\n', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Whitespace normalization error: {str(e)}")
            return text
    
    def tokenize_text(self, text: str, language: str = 'ar') -> List[str]:
        """
        Tokenize text into words
        
        Args:
            text: Input text
            language: Language code
            
        Returns:
            List[str]: List of tokens
        """
        try:
            if language == 'ar':
                # Use Arabic-specific tokenization
                tokens = araby.tokenize(text)
            else:
                # Use NLTK tokenization
                tokens = word_tokenize(text)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Text tokenization error: {str(e)}")
            return text.split()
    
    def remove_stopwords(self, tokens: List[str], language: str = 'ar') -> List[str]:
        """
        Remove stopwords from tokenized text
        
        Args:
            tokens: List of tokens
            language: Language code
            
        Returns:
            List[str]: Tokens with stopwords removed
        """
        try:
            if language == 'ar':
                # Get Arabic stopwords
                stop_words = set(stopwords.words('arabic'))
            elif language == 'en':
                # Get English stopwords
                stop_words = set(stopwords.words('english'))
            else:
                # Default to no stopwords
                return tokens
            
            # Filter out stopwords
            filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
            
            return filtered_tokens
            
        except Exception as e:
            logger.error(f"Stopword removal error: {str(e)}")
            return tokens
    
    def segment_text(self, text: str, language: str = 'ar') -> List[str]:
        """
        Segment text into sentences
        
        Args:
            text: Input text
            language: Language code
            
        Returns:
            List[str]: List of sentences
        """
        try:
            # Use NLTK sentence tokenization
            sentences = sent_tokenize(text)
            
            return sentences
            
        except Exception as e:
            logger.error(f"Text segmentation error: {str(e)}")
            # Fall back to simple segmentation
            return text.split('.')
