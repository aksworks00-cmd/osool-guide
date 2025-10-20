"""Generate missing definitions for INC items using LLM."""
import pandas as pd
import ollama
from pathlib import Path
import sys
from tqdm import tqdm
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config
from utils.logger import setup_logger


def get_definition_examples(df: pd.DataFrame, n: int = 20) -> list:
    """Get sample definitions to show the LLM the expected format."""
    with_def = df[df['DEFINITION'].notnull()]
    samples = with_def.sample(n=min(n, len(with_def)), random_state=42)

    examples = []
    for _, row in samples.iterrows():
        examples.append({
            'name': row['NAME'],
            'definition': row['DEFINITION']
        })
    return examples


def generate_definition_prompt(item_name: str, examples: list) -> str:
    """Create a prompt for the LLM to generate a definition."""

    # Format examples
    examples_text = "\n\n".join([
        f"NAME: {ex['name']}\nDEFINITION: {ex['definition']}"
        for ex in examples[:10]  # Use 10 examples
    ])

    prompt = f"""You are a NATO asset classification expert writing technical definitions for military/industrial items.

Below are examples of existing NATO item definitions to show you the expected format and style:

{examples_text}

IMPORTANT RULES:
1. Definitions must be technical and precise
2. Start with "A/An [item type/category] designed to..." or "An item consisting of..." or similar descriptive opening
3. Include purpose, function, or use case
4. Keep it concise (1-3 sentences)
5. Use formal technical language
6. May include "Excludes:" or "Includes:" statements if relevant
7. Do NOT make up specific measurements, model numbers, or technical specs unless clearly implied by the name

Now write a definition for this item:

NAME: {item_name}

Respond with ONLY the definition text, no additional commentary or JSON. Write as if you are writing an official NATO catalog entry."""

    return prompt


def generate_definition(item_name: str, examples: list, client, model: str, logger) -> str:
    """Generate a single definition using the LLM."""
    try:
        prompt = generate_definition_prompt(item_name, examples)

        response = client.chat(
            model=model,
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            options={
                'temperature': 0.3,  # Low temperature for consistent, factual output
                'num_predict': 200   # Limit response length
            }
        )

        definition = response['message']['content'].strip()

        # Clean up any markdown or extra formatting
        definition = definition.replace('**', '').replace('*', '')
        definition = definition.replace('DEFINITION:', '').strip()

        # Remove quotes if LLM wrapped it
        if definition.startswith('"') and definition.endswith('"'):
            definition = definition[1:-1]
        if definition.startswith("'") and definition.endswith("'"):
            definition = definition[1:-1]

        return definition

    except Exception as e:
        logger.error(f"Error generating definition for '{item_name}': {e}")
        return None


def generate_missing_definitions():
    """Generate definitions for all INC items that are missing them."""
    config = get_config()
    logger = setup_logger("generate_missing_definitions")

    logger.info("Starting missing definition generation process...")

    # Get file paths
    raw_data_path = config.get_path('paths.raw_data')
    inc_db_path = raw_data_path / config.get('data_files.inc_database')

    # Check if file exists
    if not inc_db_path.exists():
        logger.error(f"INC database not found: {inc_db_path}")
        return False

    # Load INC database
    logger.info(f"Loading INC database from {inc_db_path}...")
    df = pd.read_excel(inc_db_path)
    logger.info(f"Loaded {len(df)} items")

    # Find items without definitions
    missing_def = df['DEFINITION'].isnull()
    missing_count = missing_def.sum()
    logger.info(f"Found {missing_count} items without definitions")

    if missing_count == 0:
        logger.info("No missing definitions to generate!")
        return True

    # Get example definitions for the LLM
    logger.info("Preparing example definitions for LLM...")
    examples = get_definition_examples(df, n=20)
    logger.info(f"Using {len(examples)} example definitions")

    # Initialize Ollama client
    ollama_host = config.ollama_host
    model = config.ollama_model
    logger.info(f"Connecting to Ollama at {ollama_host}...")
    logger.info(f"Using model: {model}")

    client = ollama.Client(host=ollama_host)

    # Test connection
    try:
        test_response = client.chat(
            model=model,
            messages=[{'role': 'user', 'content': 'test'}]
        )
        logger.info("✓ Successfully connected to Ollama")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        logger.error("Please check:")
        logger.error("  1. Tailscale VPN is connected")
        logger.error(f"  2. Ollama server is running at {ollama_host}")
        logger.error(f"  3. Model '{model}' is available")
        return False

    # Generate definitions
    logger.info("\nGenerating definitions...")
    logger.info(f"This will take approximately {missing_count * 3 / 60:.1f} minutes (~3 sec/item)")
    logger.info("=" * 60)

    generated_count = 0
    failed_count = 0

    # Process items without definitions
    for idx in tqdm(df[missing_def].index, desc="Generating definitions"):
        item_name = df.at[idx, 'NAME']

        # Generate definition
        definition = generate_definition(item_name, examples, client, model, logger)

        if definition:
            # Update dataframe
            df.at[idx, 'DEFINITION'] = definition
            generated_count += 1

            # Log progress every 100 items
            if generated_count % 100 == 0:
                logger.info(f"Progress: {generated_count}/{missing_count} definitions generated")
                logger.info(f"Latest: {item_name[:50]}... -> {definition[:100]}...")
        else:
            failed_count += 1
            logger.warning(f"Failed to generate definition for: {item_name}")

    logger.info("\n" + "=" * 60)
    logger.info(f"✓ Generation completed!")
    logger.info(f"  Successfully generated: {generated_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info("=" * 60)

    # Save updated database
    output_path = raw_data_path / "Item Name and Definitions_QNCB_UPDATED.xlsx"
    logger.info(f"\nSaving updated database to {output_path}...")

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    logger.info(f"✓ Updated database saved to: {output_path}")

    # Show sample of generated definitions
    logger.info("\nSample of generated definitions:")
    newly_defined = df[df.index.isin(df[missing_def].index[:5])]
    for _, row in newly_defined.iterrows():
        logger.info(f"\nNAME: {row['NAME']}")
        logger.info(f"DEFINITION: {row['DEFINITION']}")

    logger.info("\n" + "=" * 60)
    logger.info("NEXT STEPS:")
    logger.info("1. Review the generated definitions in the UPDATED file")
    logger.info("2. If satisfied, replace the original file or update config.yaml")
    logger.info("3. Re-run merge_data.py to create the enriched database")
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    success = generate_missing_definitions()
    sys.exit(0 if success else 1)
