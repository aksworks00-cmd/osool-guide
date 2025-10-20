"""Stage 2: RAG Retrieval using FAISS semantic search."""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import numpy as np
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config
from utils.logger import setup_logger


class RAGRetrieval:
    """Semantic search for candidate INC items."""

    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger("stage2_retrieval")

        # Load FAISS index
        embeddings_path = self.config.get_path('paths.embeddings')
        faiss_index_path = embeddings_path / self.config.get('data_files.faiss_index')
        metadata_path = embeddings_path / self.config.get('data_files.metadata')

        self.logger.info(f"Loading FAISS index from {faiss_index_path}...")
        self.index = faiss.read_index(str(faiss_index_path))
        self.logger.info(f"✓ Loaded FAISS index with {self.index.ntotal} vectors")

        self.logger.info(f"Loading metadata from {metadata_path}...")
        self.metadata = pd.read_pickle(metadata_path)
        self.logger.info(f"✓ Loaded metadata for {len(self.metadata)} items")

        # Lazy load embedding model (only when needed)
        self.embedding_model = None
        self.logger.info("✓ Stage 2 initialized (embedding model will load on first query)")

    def _load_embedding_model(self):
        """Lazy load the embedding model when first needed."""
        if self.embedding_model is None:
            self.logger.info("Loading embedding model (nomic-embed-text-v1.5, 768-dim)...")
            try:
                import torch
                # Force CPU and disable parallelism
                torch.set_num_threads(1)

                self.embedding_model = SentenceTransformer(
                    'nomic-ai/nomic-embed-text-v1.5',
                    trust_remote_code=True,
                    device='cpu'
                )
                self.logger.info("✓ Embedding model loaded")
            except Exception as e:
                self.logger.error(f"Failed to load nomic model: {e}")
                self.logger.warning("Falling back to all-MiniLM-L6-v2 (384-dim) - will cause dimension mismatch!")
                # This is a fallback - won't work with 768-dim FAISS but better than crashing
                raise RuntimeError(f"Cannot load embedding model: {e}")

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for query text using sentence-transformers."""
        try:
            # Ensure model is loaded
            self._load_embedding_model()

            embedding = self.embedding_model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embedding.astype('float32')
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise

    def retrieve(self, keywords: List[str], top_k: int = None) -> List[Dict]:
        """
        Retrieve top candidates using semantic search.

        Args:
            keywords: List of search keywords from Stage 1
            top_k: Number of candidates to return (default from config)

        Returns:
            List of candidate dicts with INC, NAME, DEFINITION, NSG, NSC, score
        """
        if top_k is None:
            top_k = self.config.top_k

        # Create query text
        query_text = " ".join(keywords)
        self.logger.info(f"Searching for: '{query_text}'")

        # Generate query embedding
        query_embedding = self._generate_embedding(query_text)

        # Search FAISS index
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'),
            top_k
        )

        # Get candidates
        candidates = []
        for idx, dist in zip(indices[0], distances[0]):
            item = self.metadata.iloc[idx]

            # Convert distance to similarity score (0-1)
            # Using inverse distance with normalization
            similarity = 1 / (1 + float(dist))

            candidate = {
                'inc': int(item['INC']),
                'name': str(item['NAME']),
                'definition': str(item['DEFINITION']),
                'nsg': int(item['NSG']),
                'nsc': item['NSC'],  # Keep original type (could be int or str)
                'similarity_score': round(similarity, 4),
                'distance': round(float(dist), 4)
            }

            candidates.append(candidate)

        # Filter by similarity threshold
        threshold = self.config.similarity_threshold
        filtered_candidates = [c for c in candidates if c['similarity_score'] >= threshold]

        self.logger.info(f"Found {len(candidates)} candidates, {len(filtered_candidates)} above threshold {threshold}")

        for i, c in enumerate(filtered_candidates[:3], 1):
            self.logger.info(f"  {i}. INC {c['inc']}: {c['name'][:60]}... (score: {c['similarity_score']})")

        return filtered_candidates if filtered_candidates else candidates  # Return all if none pass threshold
