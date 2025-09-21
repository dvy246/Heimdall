"""
Configuration settings for the Heimdall financial analysis system.

This module handles API key validation, model initialization, and system configuration
with proper error handling and logging.
"""

from typing import Optional, List
import os
import sys
import logging
from agno.models.mistral import MistralChat
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

from src.config.logging_config import logger

# Required API keys for the financial analysis system
REQUIRED_API_KEYS = [
    "Alpha_Vantage_Stock_API",
    "FINNHUB_API_KEY",
    "SEC_API_KEY",
    "FPREP",
    "polygon_api",
    "TAVILY_API_KEY",
    "google",
    "mistral",
    "X_API_KEY"
]


def validate_api_keys() -> bool:
    """
    Validates that all required API keys are present in environment variables.

    Returns:
        bool: True if all keys are present

    Raises:
        ValueError: If any required API keys are missing
    """
    missing_keys: List[str] = []
    available_keys: List[str] = []

    for key in REQUIRED_API_KEYS:
        if os.getenv(key):
            available_keys.append(key)
        else:
            missing_keys.append(key)

    if missing_keys:
        error_msg = (
            f"API Key Validation Failed:\n"
            f"Available: {', '.join(available_keys)}\n"
            f"Missing: {', '.join(missing_keys)}"
        )
        logger.error(error_msg)
        raise ValueError(f"Missing required API keys in .env file: {', '.join(missing_keys)}")

    logger.info("All required API keys are present.")
    return True


def get_api_key(key_name: str) -> str:
    """
    Safely retrieve an API key from environment variables.

    Args:
        key_name: Name of the environment variable

    Returns:
        str: The API key value

    Raises:
        ValueError: If the API key is not found or empty
    """
    value = os.getenv(key_name)
    if not value:
        raise ValueError(f"API key '{key_name}' is not set in environment variables")
    return value


# Initialize the primary language model
model: Optional[ChatGoogleGenerativeAI] = None

try:
    google_api_key = get_api_key('google')

    # Centralized model instance to be used across the application
    model = ChatGoogleGenerativeAI(
        api_key=google_api_key,
        model='gemini-2.5-flash',  # Updated to latest stable
        temperature=0.1,  # Add some determinism for consistent
    )
    logger.info("Primary language model (Gemini) initialized successfully")

except Exception as e:
    logger.error(f"Error initializing the language model: {e}", exc_info=True)
    model = None

try:
    mistral_api=get_api_key('mistral')

    model2=MistralChat(id='mistral-large-latest',api_key=mistral_api)
    logger.info("Secondary language model (Mistral) initialized successfully")

except ValueError as e:
    logger.error(f"Configuration error: {e}")
    model2 = None
except Exception as e:
    logger.error(f"Error initializing the language model: {e}", exc_info=True)
    model2 = None

# Validate keys on startup
try:
    validate_api_keys()
    logger.info("API key validation completed successfully")
except ValueError as e:
    logger.warning(f"API key validation failed: {e}")
    logger.warning("Some features may not work properly.")

# Final model validation
if model is None:
    logger.critical("Primary model initialization failed. The system cannot function.")
    sys.exit(1)
else:
    logger.info("Heimdall configuration initialized successfully")
