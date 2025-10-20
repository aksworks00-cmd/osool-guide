"""Apply Claude-generated definitions to the INC database Excel file."""
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from data.raw.claude_definitions_batch import DEFINITIONS

def apply_definitions():
    """Apply the definitions from claude_definitions_batch.py to the Excel file."""

    # Load INC database
    raw_path = Path("data/raw")
    inc_db_path = raw_path / "Item Name and Definitions_QNCB.xlsx"

    print(f"Loading INC database from {inc_db_path}...")
    df = pd.read_excel(inc_db_path)
    print(f"Loaded {len(df)} items")

    # Count missing before
    missing_before = df['DEFINITION'].isnull().sum()
    print(f"Items without definitions before: {missing_before}")

    # Apply definitions
    update_count = 0
    for inc, definition in DEFINITIONS.items():
        # Find the row with this INC
        mask = df['INC'] == inc
        if mask.any():
            # Update the definition
            df.loc[mask, 'DEFINITION'] = definition
            update_count += 1
        else:
            print(f"Warning: INC {inc} not found in database")

    # Count missing after
    missing_after = df['DEFINITION'].isnull().sum()
    print(f"\nItems without definitions after: {missing_after}")
    print(f"Definitions applied: {update_count}")
    print(f"Definitions remaining to generate: {missing_after}")

    # Save updated database
    output_path = raw_path / "Item Name and Definitions_QNCB_UPDATED.xlsx"
    print(f"\nSaving updated database to {output_path}...")

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    print(f"✓ Updated database saved!")
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total items: {len(df)}")
    print(f"  Definitions added: {update_count}")
    print(f"  Items with definitions: {len(df) - missing_after}")
    print(f"  Items still missing definitions: {missing_after}")
    print(f"{'='*60}")

    return True


if __name__ == "__main__":
    success = apply_definitions()
    sys.exit(0 if success else 1)
