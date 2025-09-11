"""
Tests for configuration management and settings validation.
"""

import pytest
import os
from unittest.mock import patch, Mock
from src.config.settings import validate_api_keys, get_api_key
from src.config.logging_config import setup_logging, get_logger


class TestAPIKeyValidation:
    """Test suite for API key validation functionality."""

    def test_validate_api_keys_success(self, mock_env_vars):
        """Test successful API key validation."""
        result = validate_api_keys()
        assert result is True

    def test_validate_api_keys_missing_keys(self, monkeypatch):
        """Test API key validation with missing keys."""
        # Remove one required key
        monkeypatch.delenv("google", raising=False)
        
        with pytest.raises(ValueError) as exc_info:
            validate_api_keys()
        
        assert "Missing required API keys" in str(exc_info.value)
        assert "google" in str(exc_info.value)

    def test_get_api_key_success(self, mock_env_vars):
        """Test successful API key retrieval."""
        key = get_api_key("google")
        assert key == "test_google_key"

    def test_get_api_key_missing(self, monkeypatch):
        """Test API key retrieval with missing key."""
        monkeypatch.delenv("google", raising=False)
        
        with pytest.raises(ValueError) as exc_info:
            get_api_key("google")
        
        assert "API key 'google' is not set" in str(exc_info.value)


class TestLoggingConfiguration:
    """Test suite for logging configuration."""

    def test_setup_logging_default(self):
        """Test default logging setup."""
        logger = setup_logging()
        assert logger.name == "Heimdall"
        assert logger.level == 20  # INFO level

    def test_setup_logging_custom_level(self):
        """Test logging setup with custom level."""
        logger = setup_logging("DEBUG")
        assert logger.level == 10  # DEBUG level

    def test_get_logger_with_name(self):
        """Test getting logger with specific name."""
        logger = get_logger("test_module")
        assert logger.name == "Heimdall.test_module"

    def test_get_logger_without_name(self):
        """Test getting logger without name."""
        logger = get_logger()
        assert logger.name == "Heimdall"


class TestModelInitialization:
    """Test suite for model initialization."""

    @patch('src.config.settings.ChatGoogleGenerativeAI')
    def test_model_initialization_success(self, mock_model_class, mock_env_vars):
        """Test successful model initialization."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        # Import after patching
        from src.config import settings
        
        assert settings.model is not None
        mock_model_class.assert_called_once()

    def test_model_initialization_missing_key(self, monkeypatch):
        """Test model initialization with missing API key."""
        monkeypatch.delenv("google", raising=False)
        
        # This should be handled gracefully in the actual implementation
        with pytest.raises(SystemExit):
            import importlib
            from src.config import settings
            importlib.reload(settings)
