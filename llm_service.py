from groq import Groq
from config import settings
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class LLMService:
    
    def __init__(self):
        if settings.LLM_PROVIDER == "groq":
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
        # Add Ollama support if needed
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate LLM response
        
        Args:
            messages: List of {role: str, content: str}
            max_tokens: Max response tokens
            temperature: Sampling temperature
        
        Returns:
            {content: str, tokens: int, model: str}
        """
        try:
            # Format messages for API
            formatted_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            logger.info(f"LLM response generated: {tokens} tokens")
            
            return {
                "content": content,
                "tokens": tokens,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            raise Exception(f"LLM Service Error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Simple token counter (rough estimate)"""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def prepare_context(self, messages: List[dict], max_history: int = 10) -> List[Dict[str, str]]:
        """
        Prepare conversation context with sliding window
        
        Args:
            messages: All conversation messages
            max_history: Maximum messages to include
        
        Returns:
            Formatted messages for LLM
        """
        # Keep only last N messages
        recent_messages = messages[-max_history:] if len(messages) > max_history else messages
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in recent_messages
        ]
