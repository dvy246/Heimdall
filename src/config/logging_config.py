"""
Centralized logging configuration for the Heimdall application.

This module provides a standardized logging setup with both console and file output,
including log rotation and proper formatting for professional applications.
"""

import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Sets up a centralized logger for the application with professional configuration.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    log_file_path = os.path.join(logs_dir, 'heimdall.log')

    # Define professional logging format
    log_format = logging.Formatter(
        '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s | %(filename)s:%(lineno)d'
    )

    # Get the root logger
    logger = logging.getLogger('Heimdall')
    
    # Set log level from parameter
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        # Console handler with colored output for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        # File handler with rotation for production
        file_handler = TimedRotatingFileHandler(
            log_file_path, 
            when='midnight', 
            interval=1, 
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        logger.addHandler(file_handler)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'Heimdall.{name}')
    return logging.getLogger('Heimdall')


# Initialize the main application logger
logger = setup_logging()