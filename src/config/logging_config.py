import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logging():
    """
    Sets up a centralized logger for the application.
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    log_file_path = os.path.join(logs_dir, 'app.log')

    # Define logging format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
    )

    # Get the root logger
    logger = logging.getLogger('HeimdallApp')
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)

        file_handler = TimedRotatingFileHandler(
            log_file_path, when='midnight', interval=1, backupCount=7
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

    return logger

logger = setup_logging()
