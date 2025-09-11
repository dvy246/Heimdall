"""
Tests for financial data provider integrations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from src.tools.data_providers.financial_modeling_prep import (
    get_income_statements,
    get_cashflow,
    get_balance_sheet,
    get_key_metrics,
    _validate_ticker,
    _validate_period,
    FMPError
)
from src.tools.data_providers.finnhub import (
    get_insider_sentiment,
    get_analyst_recommendations,
    FinnhubError
)


class TestFinancialModelingPrep:
    """Test suite for Financial Modeling Prep API integration."""

    def test_validate_ticker_success(self):
        """Test successful ticker validation."""
        assert _validate_ticker("AAPL") == "AAPL"
        assert _validate_ticker("msft") == "MSFT"
        assert _validate_ticker(" GOOGL ") == "GOOGL"

    def test_validate_ticker_invalid(self):
        """Test ticker validation with invalid inputs."""
        with pytest.raises(ValueError):
            _validate_ticker("")
        
        with pytest.raises(ValueError):
            _validate_ticker("TOOLONGTICKERHERE")
        
        with pytest.raises(ValueError):
            _validate_ticker("INVALID@TICKER")
        
        with pytest.raises(ValueError):
            _validate_ticker(123)

    def test_validate_period_success(self):
        """Test successful period validation."""
        assert _validate_period("annual") == "annual"
        assert _validate_period("quarter") == "quarter"

    def test_validate_period_invalid(self):
        """Test period validation with invalid inputs."""
        with pytest.raises(ValueError):
            _validate_period("monthly")
        
        with pytest.raises(ValueError):
            _validate_period("yearly")

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_income_statements_success(self, mock_request, sample_financial_data):
        """Test successful income statement retrieval."""
        mock_request.return_value = sample_financial_data["data"]
        
        result = await get_income_statements("AAPL", "annual", 5)
        
        assert result["ticker"] == "AAPL"
        assert result["period"] == "annual"
        assert "data" in result
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_income_statements_api_error(self, mock_request):
        """Test income statement retrieval with API error."""
        mock_request.return_value = {"error": "API rate limit exceeded"}
        
        result = await get_income_statements("AAPL")
        
        assert "error" in result
        assert result["error"] == "API rate limit exceeded"

    @pytest.mark.asyncio
    async def test_get_income_statements_invalid_ticker(self):
        """Test income statement retrieval with invalid ticker."""
        result = await get_income_statements("")
        
        assert "error" in result
        assert "Ticker cannot be empty" in result["error"]

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_cashflow_success(self, mock_request, sample_financial_data):
        """Test successful cash flow statement retrieval."""
        mock_request.return_value = sample_financial_data["data"]
        
        result = await get_cashflow("AAPL", "quarter", 3)
        
        assert result["ticker"] == "AAPL"
        assert result["period"] == "quarter"
        assert "data" in result

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_balance_sheet_success(self, mock_request, sample_financial_data):
        """Test successful balance sheet retrieval."""
        mock_request.return_value = sample_financial_data["data"]
        
        result = await get_balance_sheet("MSFT")
        
        assert result["ticker"] == "MSFT"
        assert result["period"] == "annual"  # default
        assert "data" in result


class TestFinnhub:
    """Test suite for Finnhub API integration."""

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.finnhub._get_finnhub_client')
    async def test_get_insider_sentiment_success(self, mock_client):
        """Test successful insider sentiment retrieval."""
        mock_finnhub = Mock()
        mock_finnhub.stock_insider_sentiment.return_value = {
            "data": [{"symbol": "AAPL", "change": 100, "mspr": 0.8}]
        }
        mock_client.return_value = mock_finnhub
        
        result = await get_insider_sentiment("AAPL", "2023-01-01", "2023-12-31")
        
        assert result["ticker"] == "AAPL"
        assert "data" in result

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.finnhub._get_finnhub_client')
    async def test_get_analyst_recommendations_success(self, mock_client):
        """Test successful analyst recommendations retrieval."""
        mock_finnhub = Mock()
        mock_finnhub.recommendation_trends.return_value = [
            {"symbol": "AAPL", "buy": 15, "hold": 5, "sell": 2, "strongBuy": 8}
        ]
        mock_client.return_value = mock_finnhub
        
        result = await get_analyst_recommendations("AAPL")
        
        assert result["ticker"] == "AAPL"
        assert "recommendations" in result

    def test_finnhub_client_missing_key(self, monkeypatch):
        """Test Finnhub client initialization with missing API key."""
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        
        from src.tools.data_providers.finnhub import _get_finnhub_client
        
        with pytest.raises(FinnhubError):
            _get_finnhub_client()


class TestAPIErrorHandling:
    """Test suite for API error handling across providers."""

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_rate_limit_handling(self, mock_get):
        """Test handling of rate limit errors."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_get.return_value.__aenter__.return_value = mock_response
        
        from src.tools.data_providers.financial_modeling_prep import _execute_fmp_request
        
        result = await _execute_fmp_request(
            AsyncMock(), 
            "http://test.com", 
            {"symbol": "AAPL"}, 
            "test-endpoint", 
            "AAPL"
        )
        
        assert "error" in result
        assert "Rate limit exceeded" in result["error"]

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_network_error_handling(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")
        
        from src.tools.data_providers.financial_modeling_prep import _execute_fmp_request
        
        result = await _execute_fmp_request(
            AsyncMock(), 
            "http://test.com", 
            {"symbol": "AAPL"}, 
            "test-endpoint", 
            "AAPL"
        )
        
        assert "error" in result
        assert "Unexpected error" in result["error"]
