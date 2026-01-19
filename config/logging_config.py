"""Logging configuration"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging(log_file: str = "logs/trading.log", level: str = "INFO"):
    """Setup logging configuration"""
    
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, level))
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10_000_000, backupCount=5
    )
    file_handler.setLevel(getattr(logging, level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
