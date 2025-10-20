"""Merge NSG-NSC-INC mapping with INC database."""
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import get_config
from utils.logger import setup_logger


def merge_excel_files():
    """Merge the two Excel files on INC column."""
    config = get_config()
    logger = setup_logger("merge_data")

    logger.info("Starting data merge process...")

    # Get file paths
    raw_data_path = config.get_path('paths.raw_data')
    processed_data_path = config.get_path('paths.processed_data')
    processed_data_path.mkdir(parents=True, exist_ok=True)

    file1_name = config.get('data_files.nsg_nsc_inc_mapping')
    file2_name = config.get('data_files.inc_database')

    file1_path = raw_data_path / file1_name
    file2_path = raw_data_path / file2_name

    # Check if files exist
    if not file1_path.exists():
        logger.error(f"File not found: {file1_path}")
        logger.error("Please place your NSG-NSC-INC mapping Excel file in data/raw/")
        return False

    if not file2_path.exists():
        logger.error(f"File not found: {file2_path}")
        logger.error("Please place your INC database Excel file in data/raw/")
        return False

    # Load Excel files
    logger.info(f"Loading {file1_name}...")
    # The mapping file has multiple sheets - we need the 'Output' sheet
    df1 = pd.read_excel(file1_path, sheet_name='Output')
    logger.info(f"Loaded {len(df1)} rows from mapping file")
    logger.info(f"Columns: {list(df1.columns)}")

    logger.info(f"Loading {file2_name}...")
    df2 = pd.read_excel(file2_path)
    logger.info(f"Loaded {len(df2)} rows from INC database")
    logger.info(f"Columns: {list(df2.columns)}")

    # Merge on INC column
    logger.info("Merging dataframes on INC column...")

    # Select only needed columns from df1
    df1_subset = df1[['INC', 'NSG', 'NSC']].copy()

    # Merge
    merged = pd.merge(
        df1_subset,
        df2,
        on='INC',
        how='inner'
    )

    logger.info(f"Merged {len(merged)} rows")

    # Check for missing values
    missing_counts = merged.isnull().sum()
    if missing_counts.any():
        logger.warning("Found missing values:")
        for col, count in missing_counts.items():
            if count > 0:
                logger.warning(f"  {col}: {count} missing")

    # Handle missing DEFINITION values
    # Strategy: Fill missing definitions with empty string
    # The embedding generation will use NAME only for these items
    before_missing = merged['DEFINITION'].isnull().sum()
    if before_missing > 0:
        logger.info(f"Found {before_missing} items without DEFINITION")
        logger.info("These items will use NAME only for embedding generation")
        merged['DEFINITION'] = merged['DEFINITION'].fillna('')

    # Remove rows with missing critical values (only INC, NSG, NSC, NAME are critical)
    before_count = len(merged)
    merged = merged.dropna(subset=['INC', 'NSG', 'NSC', 'NAME'])
    after_count = len(merged)

    if before_count != after_count:
        logger.warning(f"Dropped {before_count - after_count} rows with missing critical values")

    # Ensure data types
    merged['INC'] = merged['INC'].astype(int)
    merged['NSG'] = merged['NSG'].astype(int)

    # Handle NSC - could be int or string (e.g., "2840")
    try:
        merged['NSC'] = merged['NSC'].astype(int)
    except:
        logger.info("NSC column contains non-integer values, keeping as string")

    # Reorder columns
    column_order = ['INC', 'NAME', 'DEFINITION', 'NSG', 'NSC']
    merged = merged[column_order]

    # Save enriched database
    output_path = processed_data_path / config.get('data_files.enriched_database')
    logger.info(f"Saving enriched database to {output_path}...")
    merged.to_csv(output_path, index=False)

    logger.info(f"✓ Successfully created enriched database with {len(merged)} items")
    logger.info(f"✓ Output saved to: {output_path}")

    # Display sample
    logger.info("\nSample of enriched database:")
    logger.info(merged.head().to_string())

    # Display statistics
    logger.info("\nStatistics:")
    logger.info(f"  Unique NSG values: {merged['NSG'].nunique()}")
    logger.info(f"  Unique NSC values: {merged['NSC'].nunique()}")
    logger.info(f"  Unique INC values: {merged['INC'].nunique()}")

    return True


if __name__ == "__main__":
    success = merge_excel_files()
    sys.exit(0 if success else 1)
