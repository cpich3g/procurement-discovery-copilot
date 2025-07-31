"""
Logging configuration for the Procurement Discovery Tool.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config.settings import config


def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    if log_level is None:
        log_level = config.log_level
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(funcName)s:%(lineno)d - %(message)s"
    )
    
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level))
        root_logger.addHandler(file_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("tavily").setLevel(logging.INFO)
    logging.getLogger("langchain").setLevel(logging.INFO)
    logging.getLogger("langgraph").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Initialize logging when module is imported
setup_logging()

# Application logger
logger = get_logger(__name__)
