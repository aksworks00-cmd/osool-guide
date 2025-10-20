"""Stage 3: LLM Selection of best candidate."""
import json
from typing import Dict, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config
from utils.logger import setup_logger
from utils.groq_client import get_groq_client


def format_nsc(nsg: int, nsc: int) -> str:
    """
    Format NSC without NSG prefix.
    Example: NSG=10, NSC=1005 -> '05'
             NSG=70, NSC=7010 -> '10'
    """
    nsc_str = str(nsc)
    nsg_str = str(nsg)
    if nsc_str.startswith(nsg_str):
        return nsc_str[len(nsg_str):]
    return nsc_str


class CandidateSelection:
    """Use LLM to select best matching INC from candidates."""

    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger("stage3_selection")
        self.client = get_groq_client()

    def translate_to_arabic(self, definition: str, reasoning: str) -> Dict:
        """
        Translate definition and reasoning to Arabic.
        Item name is NOT translated - it remains in English.

        Args:
            definition: Item definition in English
            reasoning: Classification reasoning in English

        Returns:
            Dict with Arabic translations (definition_ar, reasoning_ar only)
        """
        self.logger.info("Translating to Arabic...")

        prompt = f"""You are a professional translator specializing in NATO military and technical terminology.

Translate the following NATO asset classification information from English to Arabic.
Maintain technical accuracy and use appropriate military/technical terminology.

DEFINITION: {definition}
REASONING: {reasoning}

Respond ONLY with valid JSON in this exact format:
{{
  "definition_ar": "Arabic translation of definition",
  "reasoning_ar": "Arabic translation of reasoning"
}}

IMPORTANT:
- Keep acronyms like NSG, NSC, INC, NATO in English
- Translate technical terms accurately
- Use formal Arabic (Modern Standard Arabic)
- Maintain the same meaning and tone
- DO NOT translate item names - they stay in English"""

        try:
            # Use Groq's JSON completion method
            result = self.client.chat_completion_json(
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a professional Arabic translator. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                temperature=0.1
            )

            self.logger.info("✓ Translation completed")
            return result

        except Exception as e:
            self.logger.error(f"Error in translation: {e}")
            return {
                'definition_ar': '',
                'reasoning_ar': ''
            }

    def select_best_match(self, user_query: str, candidates: List[Dict]) -> Dict:
        """
        Select the best matching INC from retrieved candidates.

        Args:
            user_query: Original user query
            candidates: List of candidate dicts from Stage 2

        Returns:
            Dict with selected INC, NSG, NSC, confidence, and reasoning
        """
        self.logger.info(f"Selecting best match from {len(candidates)} candidates")

        if not candidates:
            self.logger.error("No candidates provided!")
            return None

        # If only one candidate, return it with high confidence
        if len(candidates) == 1:
            c = candidates[0]
            self.logger.info(f"Only one candidate: INC {c['inc']}")

            reasoning = 'Only candidate retrieved'

            # Translate to Arabic (definition and reasoning only, NOT name)
            translations = self.translate_to_arabic(
                c['definition'],
                reasoning
            )

            return {
                'inc': c['inc'],
                'nsg': c['nsg'],
                'nsc': c['nsc'],
                'nsc_formatted': format_nsc(c['nsg'], c['nsc']),
                'name': c['name'],  # Name stays in English
                'definition': c['definition'],
                'definition_ar': translations.get('definition_ar', ''),
                'confidence': min(c['similarity_score'] * 1.1, 0.99),  # Boost slightly
                'reasoning': reasoning,
                'reasoning_ar': translations.get('reasoning_ar', '')
            }

        # Format candidates for LLM
        candidates_text = ""
        for i, c in enumerate(candidates, 1):
            # Truncate definition if too long
            definition = c['definition']
            if len(definition) > 300:
                definition = definition[:300] + "..."

            candidates_text += f"""{i}. INC: {c['inc']}
   NAME: {c['name']}
   NSG: {c['nsg']}, NSC: {c['nsc']}
   SIMILARITY: {c['similarity_score']}
   DEFINITION: {definition}

"""

        prompt = f"""You are a NATO asset classification expert.

User has this item: "{user_query}"

Retrieved candidates from database:
{candidates_text}

Analyze which INC is the best match for the user's item. Consider:
1. Name similarity to user's description
2. Definition relevance
3. Specific details mentioned by user

Respond ONLY with valid JSON in this exact format:
{{
  "selected_inc": "00000",
  "confidence": 0.95,
  "reasoning": "brief explanation of why this is the best match"
}}

Choose the INC number from the candidates above. Confidence should be 0.0-1.0."""

        try:
            # Use Groq's JSON completion method
            result = self.client.chat_completion_json(
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a NATO logistics expert. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                temperature=0.1
            )

            # Find the selected candidate
            selected_inc = str(result['selected_inc'])
            selected = None
            for c in candidates:
                if str(c['inc']) == selected_inc:
                    selected = c
                    break

            if selected is None:
                self.logger.warning(f"LLM selected INC {selected_inc} not in candidates, using first candidate")
                selected = candidates[0]
                result['confidence'] = selected['similarity_score']
                result['reasoning'] = "Fallback to highest similarity candidate"

            self.logger.info(f"Selected INC {selected['inc']}: {selected['name']}")
            self.logger.info(f"Confidence: {result['confidence']:.2%}")
            self.logger.info(f"Reasoning: {result['reasoning']}")

            # Translate to Arabic (definition and reasoning only, NOT name)
            translations = self.translate_to_arabic(
                selected['definition'],
                result['reasoning']
            )

            return {
                'inc': selected['inc'],
                'nsg': selected['nsg'],
                'nsc': selected['nsc'],
                'nsc_formatted': format_nsc(selected['nsg'], selected['nsc']),
                'name': selected['name'],  # Name stays in English
                'definition': selected['definition'],
                'definition_ar': translations.get('definition_ar', ''),
                'confidence': float(result['confidence']),
                'reasoning': result['reasoning'],
                'reasoning_ar': translations.get('reasoning_ar', '')
            }

        except Exception as e:
            self.logger.error(f"Error in candidate selection: {e}")
            # Fallback: return highest similarity candidate
            selected = candidates[0]
            reasoning = 'Fallback to highest similarity (error in selection)'

            # Translate to Arabic (definition and reasoning only, NOT name)
            translations = self.translate_to_arabic(
                selected['definition'],
                reasoning
            )

            return {
                'inc': selected['inc'],
                'nsg': selected['nsg'],
                'nsc': selected['nsc'],
                'nsc_formatted': format_nsc(selected['nsg'], selected['nsc']),
                'name': selected['name'],  # Name stays in English
                'definition': selected['definition'],
                'definition_ar': translations.get('definition_ar', ''),
                'confidence': selected['similarity_score'],
                'reasoning': reasoning,
                'reasoning_ar': translations.get('reasoning_ar', '')
            }
