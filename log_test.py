import logging
from pathlib import Path

# 1. Elegantly get the current directory using pathlib
current_dir = Path(__file__).parent
log_file = current_dir / "scanner.log"

# 2. Configure logging (output to both screen and file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'), # Write to file
        logging.StreamHandler()                          # Print to screen
    ]
)

# 3. Test it out
logging.info("Ghost protocol initiated, starting scan...")
logging.warning("Unknown process detected occupying port 8081!")
try:
    result = 1 / 0
except Exception as e:
    logging.error(f"Fatal error occurred: {e}")