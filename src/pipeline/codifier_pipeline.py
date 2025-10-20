"""Main three-stage codification pipeline."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from pipeline.stage1_understanding import QueryUnderstanding
from pipeline.stage2_retrieval import RAGRetrieval
from pipeline.stage3_selection import CandidateSelection
from utils.logger import setup_logger


class NATOCodifierPipeline:
    """Complete three-stage NATO asset codification pipeline."""

    def __init__(self):
        self.logger = setup_logger("codifier_pipeline")
        self.logger.info("Initializing NATO Codifier Pipeline...")

        try:
            # Initialize all stages
            self.stage1 = QueryUnderstanding()
            self.stage2 = RAGRetrieval()
            self.stage3 = CandidateSelection()

            self.logger.info("✓ Pipeline initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize pipeline: {e}")
            raise

    def codify(self, user_query: str) -> dict:
        """
        Run complete codification pipeline.

        Args:
            user_query: User's description of the asset

        Returns:
            Dict with INC, NSC, NSG, name, confidence, reasoning
        """
        self.logger.info("="*70)
        self.logger.info(f"CODIFYING: {user_query}")
        self.logger.info("="*70)

        try:
            # Stage 1: Query Understanding
            self.logger.info("\n[STAGE 1] Query Understanding")
            self.logger.info("-" * 70)
            query_info = self.stage1.understand_query(user_query)
            keywords = query_info.get('search_keywords', [])

            if not keywords:
                self.logger.warning("No keywords extracted, using raw query")
                keywords = user_query.lower().split()

            # Stage 2: RAG Retrieval
            self.logger.info("\n[STAGE 2] RAG Retrieval")
            self.logger.info("-" * 70)
            candidates = self.stage2.retrieve(keywords)

            if not candidates:
                self.logger.error("No candidates found!")
                return {
                    'success': False,
                    'error': 'No matching items found in database'
                }

            # Stage 3: Candidate Selection
            self.logger.info("\n[STAGE 3] Candidate Selection")
            self.logger.info("-" * 70)
            result = self.stage3.select_best_match(user_query, candidates)

            if result:
                self.logger.info("\n" + "="*70)
                self.logger.info("CODIFICATION COMPLETE")
                self.logger.info("="*70)
                result['success'] = True
                result['query'] = user_query
                return result
            else:
                return {
                    'success': False,
                    'error': 'Failed to select best match'
                }

        except Exception as e:
            self.logger.error(f"Error in pipeline: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def format_result(self, result: dict) -> str:
        """Format result as human-readable string."""
        if not result.get('success', False):
            return f"❌ Error: {result.get('error', 'Unknown error')}"

        # Confidence emoji
        confidence = result.get('confidence', 0)
        if confidence >= 0.9:
            conf_emoji = "🟢"
        elif confidence >= 0.75:
            conf_emoji = "🟡"
        else:
            conf_emoji = "🟠"

        output = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                     NATO ASSET CODIFICATION                          ║
╚══════════════════════════════════════════════════════════════════════╝

Query: {result['query']}

NATO Classification:
  ├─ NSG: {result['nsg']} (NATO Supply Group)
  ├─ NSC: {result['nsc']} (NATO Supply Class)
  └─ INC: {result['inc']} (Item Name Code)

Item Name: {result['name']}

Confidence: {conf_emoji} {confidence:.1%}

Reasoning: {result['reasoning']}

────────────────────────────────────────────────────────────────────────
"""
        return output
