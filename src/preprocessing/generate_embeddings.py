"""Generate embeddings for INC database using nomic-embed-text via Ollama."""
import pandas as pd
import numpy as np
import pickle
import faiss
from pathlib import Path
import sys
from tqdm import tqdm
import ollama

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config
from utils.logger import setup_logger


def generate_embedding(text: str, client, model: str, max_retries: int = 3) -> np.ndarray:
    """Generate embedding for a single text using Ollama with retry logic."""
    for attempt in range(max_retries):
        try:
            response = client.embeddings(model=model, prompt=text)
            return np.array(response['embedding'], dtype='float32')
        except Exception as e:
            if attempt < max_retries - 1:
                # Wait before retrying (exponential backoff)
                import time
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait_time)
                continue
            else:
                raise Exception(f"Error generating embedding after {max_retries} attempts: {e}")


def generate_embeddings():
    """Generate embeddings for all INC items and create FAISS index."""
    config = get_config()
    logger = setup_logger("generate_embeddings")

    logger.info("Starting embedding generation process...")

    # Setup paths
    processed_data_path = config.get_path('paths.processed_data')
    embeddings_path = config.get_path('paths.embeddings')
    embeddings_path.mkdir(parents=True, exist_ok=True)

    enriched_db_path = processed_data_path / config.get('data_files.enriched_database')

    # Check if enriched database exists
    if not enriched_db_path.exists():
        logger.error(f"Enriched database not found: {enriched_db_path}")
        logger.error("Please run merge_data.py first!")
        return False

    # Load enriched database
    logger.info(f"Loading enriched database from {enriched_db_path}...")
    df = pd.read_csv(enriched_db_path)
    logger.info(f"Loaded {len(df)} items")

    # Initialize Ollama client
    ollama_host = config.ollama_host
    embedding_model = config.embedding_model
    logger.info(f"Connecting to Ollama at {ollama_host}...")
    logger.info(f"Using embedding model: {embedding_model}")

    # Configure Ollama client with custom host
    client = ollama.Client(host=ollama_host)

    # Test connection
    try:
        test_embedding = generate_embedding("test", client, embedding_model)
        embedding_dim = len(test_embedding)
        logger.info(f"✓ Successfully connected to Ollama")
        logger.info(f"✓ Embedding dimension: {embedding_dim}")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        logger.error("Please check:")
        logger.error("  1. Tailscale VPN is connected")
        logger.error(f"  2. Ollama server is running at {ollama_host}")
        logger.error(f"  3. Model '{embedding_model}' is available")
        return False

    # Generate embeddings
    logger.info("Generating embeddings...")
    logger.info("This may take several hours for large datasets...")

    embeddings = []
    batch_size = config.get('embedding.batch_size', 100)

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Generating embeddings"):
        # Combine NAME and DEFINITION for embedding
        # If DEFINITION is empty, use NAME only
        name = str(row['NAME']).strip()
        definition = str(row['DEFINITION']).strip()

        if definition and definition != 'nan':
            text = f"{name} {definition}"
        else:
            text = name

        # Generate embedding
        try:
            embedding = generate_embedding(text, client, embedding_model)
            embeddings.append(embedding)
        except Exception as e:
            logger.error(f"Error processing INC {row['INC']}: {e}")
            # Use zero vector as fallback
            embeddings.append(np.zeros(embedding_dim, dtype='float32'))

        # Log progress every batch_size items
        if (idx + 1) % batch_size == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} items")

    # Convert to numpy array
    embeddings_array = np.array(embeddings).astype('float32')
    logger.info(f"✓ Generated {len(embeddings_array)} embeddings")
    logger.info(f"✓ Shape: {embeddings_array.shape}")

    # Create FAISS index
    logger.info("Creating FAISS index...")
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(embeddings_array)
    logger.info(f"✓ FAISS index created with {index.ntotal} vectors")

    # Save FAISS index
    faiss_index_path = embeddings_path / config.get('data_files.faiss_index')
    logger.info(f"Saving FAISS index to {faiss_index_path}...")
    faiss.write_index(index, str(faiss_index_path))
    logger.info("✓ FAISS index saved")

    # Save metadata (dataframe)
    metadata_path = embeddings_path / config.get('data_files.metadata')
    logger.info(f"Saving metadata to {metadata_path}...")
    df.to_pickle(metadata_path)
    logger.info("✓ Metadata saved")

    logger.info("\n" + "="*60)
    logger.info("Embedding generation completed successfully!")
    logger.info("="*60)
    logger.info(f"Total items processed: {len(df)}")
    logger.info(f"FAISS index: {faiss_index_path}")
    logger.info(f"Metadata: {metadata_path}")
    logger.info("\nYou can now run the main pipeline!")

    return True


if __name__ == "__main__":
    success = generate_embeddings()
    sys.exit(0 if success else 1)
