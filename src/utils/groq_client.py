"""Groq API client wrapper with caching and error handling."""
import os
import json
from groq import Groq
from typing import List, Dict, Optional
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GroqClient:
    """Wrapper for Groq API with retry logic and caching support."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key (if None, reads from GROQ_API_KEY env var)
            model: Model to use (default: llama-3.3-70b-versatile)
        """
        self.api_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found. Set it in .env or pass as argument.")

        self.client = Groq(api_key=self.api_key)
        self.model = model

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        max_retries: int = 3
    ) -> str:
        """
        Send chat completion request to Groq.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            max_retries: Number of retry attempts on failure

        Returns:
            Response content as string
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"Groq API error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Groq API failed after {max_retries} attempts: {e}")

    def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        max_retries: int = 3
    ) -> Dict:
        """
        Send chat completion request expecting JSON response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_retries: Number of retry attempts

        Returns:
            Parsed JSON response as dict
        """
        response_text = self.chat_completion(messages, temperature, max_tokens, max_retries)

        # Clean up markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        return json.loads(response_text.strip())


# Global client instance (singleton)
_groq_client = None


def get_groq_client() -> GroqClient:
    """Get or create global Groq client instance."""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
