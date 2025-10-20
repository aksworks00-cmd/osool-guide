"""Stage 1: Query Understanding using LLM."""
import json
from typing import Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config
from utils.logger import setup_logger
from utils.groq_client import get_groq_client


class QueryUnderstanding:
    """Extract keywords and item characteristics from user query."""

    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger("stage1_understanding")
        self.client = get_groq_client()

    def understand_query(self, user_query: str) -> Dict:
        """
        Analyze user query and extract key information.

        Args:
            user_query: User's description of the item

        Returns:
            Dict with extracted information
        """
        self.logger.info(f"Understanding query: '{user_query}'")

        prompt = f"""You are a NATO asset classification expert.

User has this item: "{user_query}"

IMPORTANT - Query Normalization:
- Focus on the PRIMARY function/type of the item, not word order
- "computer desktop" = "desktop computer" (ADP/computing equipment)
- "computer desk" = furniture for holding a computer
- "phone mobile" = "mobile phone" (communications equipment)
- "printer laser" = "laser printer" (office equipment)
- Identify the CORE item first, then modifiers

Extract key information to help search the NATO database:
1. Item category (vehicle, aircraft part, electronic component, clothing, weapon, office equipment, furniture, etc.)
2. Specific item type (what IS it primarily?)
3. Key characteristics and features
4. 5-7 search keywords that best describe this item's PRIMARY FUNCTION

Respond ONLY with valid JSON in this exact format:
{{
  "category": "item category",
  "item_type": "specific type",
  "characteristics": ["characteristic1", "characteristic2"],
  "search_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}"""

        try:
            # Use Groq API for chat completion
            response_text = self.client.chat_completion(
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a NATO logistics classification expert. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                temperature=0.1
            )

            # Handle potential markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())

            self.logger.info(f"Category: {result.get('category')}")
            self.logger.info(f"Item type: {result.get('item_type')}")
            self.logger.info(f"Keywords: {result.get('search_keywords')}")

            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            self.logger.error(f"Response was: {response_text}")
            # Fallback: use raw query as keywords
            return {
                "category": "unknown",
                "item_type": "unknown",
                "characteristics": [],
                "search_keywords": user_query.lower().split()
            }
        except Exception as e:
            self.logger.error(f"Error in query understanding: {e}")
            raise
