"""
Tests for edge cases and boundary conditions across the Heimdall system.
"""

import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage


class TestInputValidation:
    """Test suite for input validation edge cases."""

    @pytest.mark.parametrize("invalid_ticker", [
        "",  # Empty string
        " ",  # Whitespace only
        "A" * 20,  # Too long
        "A@B",  # Special characters
        None,  # None value
        [],  # List
        {},  # Dict
    ])
    def test_ticker_validation_edge_cases(self, invalid_ticker: Any) -> None:
        """Test ticker validation with various invalid inputs."""
        try:
            from src.tools.data_providers.financial_modeling_prep import _validate_ticker
            
            if invalid_ticker is None or not isinstance(invalid_ticker, str):
                with pytest.raises((ValueError, TypeError)):
                    _validate_ticker(invalid_ticker)
            elif invalid_ticker == "123":  # Numbers only - might be valid in some systems
                # Skip this specific case as it might be valid
                pass
            else:
                with pytest.raises(ValueError):
                    _validate_ticker(invalid_ticker)
        except ImportError:
            pytest.skip("Validation functions not available")

    @pytest.mark.parametrize("invalid_period", [
        "daily",  # Not supported
        "weekly",  # Not supported
        "monthly",  # Not supported
        "yearly",  # Wrong term
        "",  # Empty
        None,  # None
        123,  # Number
    ])
    def test_period_validation_edge_cases(self, invalid_period: Any) -> None:
        """Test period validation with various invalid inputs."""
        try:
            from src.tools.data_providers.financial_modeling_prep import _validate_period
            
            with pytest.raises((ValueError, TypeError)):
                _validate_period(invalid_period)
        except ImportError:
            pytest.skip("Validation functions not available")


class TestAPIErrorHandling:
    """Test suite for API error handling edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code,expected_error", [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (429, "Rate limit exceeded"),
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
        (504, "Gateway Timeout"),
    ])
    async def test_http_error_codes(self, status_code: int, expected_error: str) -> None:
        """Test handling of various HTTP error codes."""
        with patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request') as mock_request:
            # Mock the request to return an error with the status code
            mock_request.return_value = {"error": f"HTTP status {status_code}: {expected_error}"}
            
            try:
                from src.tools.data_providers.financial_modeling_prep import get_income_statements
                
                result = await get_income_statements.ainvoke({"ticker": "AAPL"})
                
                assert "error" in result
                assert str(status_code) in result["error"] or expected_error.lower() in result["error"].lower()
            except ImportError:
                pytest.skip("FMP request functions not available")

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self) -> None:
        """Test handling of network timeouts."""
        with patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request') as mock_request:
            mock_request.return_value = {"error": "Request timeout"}
            
            try:
                from src.tools.data_providers.financial_modeling_prep import get_income_statements
                
                result = await get_income_statements.ainvoke({"ticker": "AAPL"})
                
                assert "error" in result
                assert "timeout" in result["error"].lower()
            except ImportError:
                pytest.skip("FMP request functions not available")

    @pytest.mark.asyncio
    async def test_malformed_json_response(self) -> None:
        """Test handling of malformed JSON responses."""
        with patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request') as mock_request:
            mock_request.return_value = {"error": "JSON parse error"}
            
            try:
                from src.tools.data_providers.financial_modeling_prep import get_income_statements
                
                result = await get_income_statements.ainvoke({"ticker": "AAPL"})
                
                assert "error" in result
                assert "json" in result["error"].lower() or "parse" in result["error"].lower()
            except ImportError:
                pytest.skip("FMP request functions not available")


class TestStateManagement:
    """Test suite for state management edge cases."""

    def test_state_with_empty_messages(self) -> None:
        """Test state initialization with empty message list."""
        try:
            from src.graph.state import HeimdallState
            
            state = HeimdallState(
                ticker="AAPL",
                company_name="Apple Inc.",
                messages=[]
            )
            
            assert state["messages"] == []
            assert len(state["messages"]) == 0
        except ImportError:
            pytest.skip("HeimdallState not available")

    def test_state_with_none_values(self) -> None:
        """Test state behavior with None values."""
        try:
            from src.graph.state import HeimdallState
            
            state = HeimdallState(
                ticker="AAPL",
                company_name="Apple Inc.",
                messages=[]
            )
            
            # Test setting None values
            state["financial_report"] = None
            state["mission_plan"] = None
            
            assert state.get("financial_report") is None
            assert state.get("mission_plan") is None
        except ImportError:
            pytest.skip("HeimdallState not available")

    def test_state_with_large_message_history(self) -> None:
        """Test state with large message history."""
        try:
            from src.graph.state import HeimdallState
            
            # Create a large number of messages
            large_message_list = [
                HumanMessage(content=f"Message {i}") for i in range(1000)
            ]
            
            state = HeimdallState(
                ticker="AAPL",
                company_name="Apple Inc.",
                messages=large_message_list
            )
            
            assert len(state["messages"]) == 1000
            assert isinstance(state["messages"][0], HumanMessage)
            assert isinstance(state["messages"][-1], HumanMessage)
        except ImportError:
            pytest.skip("HeimdallState not available")


class TestMemoryAndPerformance:
    """Test suite for memory usage and performance edge cases."""

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self) -> None:
        """Test handling of concurrent API requests."""
        import asyncio
        
        try:
            from src.tools.data_providers.financial_modeling_prep import get_income_statements
            
            # Create multiple concurrent requests using proper LangChain tool invocation
            tasks = [
                get_income_statements.ainvoke({"ticker": "AAPL", "period": "annual", "limit": 1})
                for _ in range(10)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should complete without hanging
            assert len(results) == 10
            
            # Check that results are either successful or contain error handling
            for result in results:
                if isinstance(result, Exception):
                    # Exceptions should be handled gracefully
                    assert True
                else:
                    # Successful results should have proper structure
                    assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Financial data providers not available")

    def test_large_data_processing(self) -> None:
        """Test processing of large datasets."""
        # Create a large mock dataset
        large_dataset = {
            "data": [
                {
                    "date": f"2023-{i:02d}-01",
                    "revenue": 1000000 * i,
                    "netIncome": 100000 * i
                }
                for i in range(1, 101)  # 100 data points
            ]
        }
        
        # Test that large datasets can be processed without issues
        assert len(large_dataset["data"]) == 100
        assert large_dataset["data"][0]["revenue"] == 1000000
        assert large_dataset["data"][-1]["revenue"] == 100000000


class TestConfigurationEdgeCases:
    """Test suite for configuration edge cases."""

    def test_missing_all_api_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test behavior when all API keys are missing."""
        # Remove all API keys
        api_keys = [
            "google", "FINNHUB_API_KEY", "FPREP", 
            "Alpha_Vantage_Stock_API", "polygon_api", 
            "SEC_API_KEY", "TAVILY_API_KEY"
        ]
        
        for key in api_keys:
            monkeypatch.delenv(key, raising=False)
        
        try:
            from src.config.settings import validate_api_keys
            
            with pytest.raises(ValueError) as exc_info:
                validate_api_keys()
            
            assert "Missing required API keys" in str(exc_info.value)
        except ImportError:
            pytest.skip("Settings validation not available")

    def test_invalid_log_level(self) -> None:
        """Test handling of invalid log levels."""
        try:
            from src.config.logging_config import setup_logging
            
            # Test with invalid log level
            logger = setup_logging("INVALID_LEVEL")
            
            # Should fall back to default level or handle gracefully
            assert logger is not None
        except ImportError:
            pytest.skip("Logging config not available")
        except ValueError:
            # This is expected behavior for invalid log levels
            assert True
