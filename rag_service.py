from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict
from config import settings
import logging

logger = logging.getLogger(__name__)

class RAGService:
    
    def __init__(self):
        # Load embedding model (runs locally)
        logger.info("✓ RAG Service initialized")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded")
    
    def chunk_text(self, text: str, chunk_size: int = None) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Input text
            chunk_size: Characters per chunk
        
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        words = text.split()
        chunks = []
        
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text chunks"""
        embeddings = self.embedding_model.encode(texts)
        logger.info(f"Generated embeddings for {len(texts)} texts")
        return embeddings
    
    def retrieve_relevant_chunks(
        self, 
        query: str, 
        document_chunks: List[Dict],
        top_k: int = None
    ) -> List[Dict]:
        """
        Retrieve most relevant chunks for query
        
        Args:
            query: User question
            document_chunks: List of {text, embedding, chunk_id}
            top_k: Number of chunks to return
        
        Returns:
            Top K relevant chunks with scores
        """
        top_k = top_k or settings.TOP_K
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Extract chunk embeddings
        chunk_embeddings = np.array([chunk["embedding"] for chunk in document_chunks])
        
        # Calculate cosine similarity
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        
        # Get top K indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return top chunks with scores
        results = []
        for idx in top_indices:
            results.append({
                "text": document_chunks[idx]["text"],
                "chunk_id": document_chunks[idx]["chunk_id"],
                "score": float(similarities[idx])
            })
        
        logger.info(f"Retrieved {len(results)} relevant chunks")
        return results
    
    def build_rag_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """Build prompt with retrieved context"""
        context = "\n\n".join([
            f"Context {i+1}:\n{chunk['text']}"
            for i, chunk in enumerate(retrieved_chunks)
        ])
        
        prompt = f"""Based on the following context, answer the question.

{context}

Question: {query}

Answer based only on the provided context:"""
        
        return prompt
