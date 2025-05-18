"""
Embedding service for the LLM Training Platform.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional, Union
from loguru import logger

# Import embedding models
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Service for generating embeddings from text."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the embedding model to use
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize model
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            
            # Check if it's a sentence-transformers model
            if "sentence-transformers" in self.model_name or "/" in self.model_name:
                self.model = SentenceTransformer(self.model_name, device=self.device)
                logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
            else:
                # Load HuggingFace model and tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
                logger.info(f"Loaded HuggingFace model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List[np.ndarray]: List of embeddings as numpy arrays
        """
        try:
            if not texts:
                return []
            
            # Check if model is loaded
            if self.model is None:
                self._load_model()
            
            # Generate embeddings
            if isinstance(self.model, SentenceTransformer):
                # Use SentenceTransformer
                embeddings = self.model.encode(texts, convert_to_numpy=True)
                return list(embeddings)
            else:
                # Use HuggingFace model
                embeddings = []
                
                for text in texts:
                    # Tokenize and prepare input
                    inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # Generate embedding
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                    
                    # Use mean pooling to get sentence embedding
                    attention_mask = inputs["attention_mask"]
                    token_embeddings = outputs.last_hidden_state
                    
                    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                    embedding = (sum_embeddings / sum_mask).squeeze().cpu().numpy()
                    
                    embeddings.append(embedding)
                
                return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            np.ndarray: Embedding as numpy array
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else np.array([])
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            float: Cosine similarity score
        """
        # Normalize embeddings
        embedding1_norm = embedding1 / np.linalg.norm(embedding1)
        embedding2_norm = embedding2 / np.linalg.norm(embedding2)
        
        # Compute cosine similarity
        similarity = np.dot(embedding1_norm, embedding2_norm)
        
        return float(similarity)
    
    def compute_similarities(self, query_embedding: np.ndarray, embeddings: List[np.ndarray]) -> List[float]:
        """
        Compute cosine similarities between a query embedding and a list of embeddings.
        
        Args:
            query_embedding: Query embedding
            embeddings: List of embeddings to compare against
            
        Returns:
            List[float]: List of cosine similarity scores
        """
        # Normalize query embedding
        query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
        
        # Compute similarities
        similarities = []
        
        for embedding in embeddings:
            # Normalize embedding
            embedding_norm = embedding / np.linalg.norm(embedding)
            
            # Compute cosine similarity
            similarity = np.dot(query_embedding_norm, embedding_norm)
            similarities.append(float(similarity))
        
        return similarities


# Arabic-specific embedding models
class ArabicEmbeddingService(EmbeddingService):
    """Service for generating embeddings from Arabic text."""
    
    def __init__(self, model_name: str = "UBC-NLP/ARBERT"):
        """
        Initialize the Arabic embedding service.
        
        Args:
            model_name: Name of the Arabic embedding model to use
        """
        # Default Arabic models:
        # - UBC-NLP/ARBERT
        # - CAMeL-Lab/bert-base-arabic-camelbert-mix
        # - BAAI/bge-m3
        super().__init__(model_name=model_name)
