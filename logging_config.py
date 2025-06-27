# logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configure logging with console and rotating file handlers.
    Logs are stored in ~/Documents/SwiftSale/swiftsale.log.
    """
    # Define log directory and file
    log_dir = os.path.join(os.path.expanduser("~"), "Documents", "SwiftSale")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "swiftsale.log")

    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    # File handler with rotation (5MB per file, max 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.info("Logging configured successfully")