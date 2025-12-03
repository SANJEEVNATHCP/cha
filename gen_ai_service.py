"""Service for Google Generative AI (Gemini) integration."""
import google.generativeai as genai
from typing import List, Optional, AsyncGenerator
from app.config.settings import settings


class GenAIService:
    """Service to interact with Google Generative AI models."""
    
    def __init__(self):
        """Initialize the service with API key."""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def generate_response(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response from the Gen AI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        try:
            # Convert messages to prompt format for Gemini
            prompt = self._format_messages_for_gemini(messages)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens or 1024,
                ),
            )
            
            return response.text
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    async def stream_response(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the Gen AI model.
        
        Args:
            messages: List of message dictionaries
            temperature: Controls randomness
            max_tokens: Maximum tokens
            
        Yields:
            Text chunks of the response
        """
        try:
            prompt = self._format_messages_for_gemini(messages)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens or 1024,
                ),
                stream=True,
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Error streaming response: {str(e)}")
    
    def _format_messages_for_gemini(self, messages: List[dict]) -> str:
        """Convert message list to Gemini-compatible format."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        return "\n".join(formatted) + "\nAssistant:"


# Global service instance
gen_ai_service = GenAIService()
