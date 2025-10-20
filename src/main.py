"""Main CLI interface for NATO Asset Codifier."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from pipeline.codifier_pipeline import NATOCodifierPipeline
from utils.logger import setup_logger


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                    NATO ASSET CODIFIER                               ║
║                                                                      ║
║  Classify physical assets using NATO codes (INC + NSC + NSG)        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Commands:
  - Enter asset description to classify
  - /help    - Show this help
  - /exit    - Quit application

Examples:
  "Boeing 737 gas turbine accessory module"
  "Fixed paper capacitor for radio"
  "Toyota Land Cruiser 4x4"

────────────────────────────────────────────────────────────────────────
"""
    print(banner)


def print_help():
    """Print help information."""
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                              HELP                                    ║
╚══════════════════════════════════════════════════════════════════════╝

How to use:
1. Describe the physical asset you have
2. Be as specific as possible (manufacturer, model, type)
3. System will return NATO codes (NSG, NSC, INC)

Commands:
  /help     - Show this help
  /exit     - Quit application

Tips for best results:
  ✓ Include item type: "turbine module" not just "module"
  ✓ Include application: "aircraft engine" vs "vehicle engine"
  ✓ Include specifications: "fixed paper capacitor" not just "capacitor"
  ✓ Commercial names OK: "Toyota Land Cruiser" → "TRUCK,UTILITY"

Examples:
  Good: "Boeing 737 CFM56 turbine accessory section module"
  Okay: "Aircraft gas turbine accessory module"
  Poor: "Some airplane part"

────────────────────────────────────────────────────────────────────────
"""
    print(help_text)


def main():
    """Main CLI loop."""
    logger = setup_logger("main")

    # Print banner
    print_banner()

    # Initialize pipeline
    print("Initializing NATO Codifier Pipeline...")
    print("(This may take a few seconds on first run)\n")

    try:
        pipeline = NATOCodifierPipeline()
        print("✓ Pipeline ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        print("\nPlease check:")
        print("  1. Ollama server is running (http://100.99.83.98:11434)")
        print("  2. Embeddings have been generated (run generate_embeddings.py)")
        print("  3. Configuration is correct (config/config.yaml)")
        return 1

    # Main loop
    while True:
        try:
            # Get user input
            user_input = input("\n🔍 Asset description (or /help, /exit): ").strip()

            # Handle empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == '/exit':
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == '/help':
                print_help()
                continue

            # Process query
            print(f"\n🔄 Processing: {user_input}\n")
            result = pipeline.codify(user_input)

            # Display result
            print(pipeline.format_result(result))

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")
            print("Please try again or type /exit to quit\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
