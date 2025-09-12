"""Tests for financial data provider integrations."""

import pytest
import asyncio
from typing import Dict, Any
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
    get_insiders_sentiment,
    get_analyst_recommendation,
    FinnhubError
)


class TestFinancialModelingPrep:
    """Test suite for Financial Modeling Prep API integration."""

    def test_validate_ticker_success(self) -> None:
        """Test successful ticker validation."""
        assert _validate_ticker("AAPL") == "AAPL"
        assert _validate_ticker("msft") == "MSFT"
        assert _validate_ticker(" GOOGL ") == "GOOGL"

    def test_validate_ticker_invalid(self) -> None:
        """Test ticker validation with invalid inputs."""
        with pytest.raises(ValueError):
            _validate_ticker("")
        
        with pytest.raises(ValueError):
            _validate_ticker("TOOLONGTICKERHERE")
        
        with pytest.raises(ValueError):
            _validate_ticker("INVALID@TICKER")
        
        with pytest.raises(ValueError):
            _validate_ticker(123)

    def test_validate_period_success(self) -> None:
        """Test successful period validation."""
        assert _validate_period("annual") == "annual"
        assert _validate_period("quarter") == "quarter"

    def test_validate_period_invalid(self) -> None:
        """Test period validation with invalid inputs."""
        with pytest.raises(ValueError):
            _validate_period("monthly")
        
        with pytest.raises(ValueError):
            _validate_period("yearly")

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_income_statements_success(self, mock_request: AsyncMock, sample_financial_data: Dict[str, Any]) -> None:
        """Test successful income statement retrieval."""
        mock_request.return_value = sample_financial_data["data"]
        
        result = await get_income_statements.ainvoke({"ticker": "AAPL", "period": "annual", "limit": 5})
        
        assert result["ticker"] == "AAPL"
        assert result["period"] == "annual"
        assert "data" in result
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_income_statements_api_error(self, mock_request: AsyncMock) -> None:
        """Test income statement retrieval with API error."""
        mock_request.return_value = {"error": "API rate limit exceeded"}
        
        result = await get_income_statements.ainvoke({"ticker": "AAPL"})
        
        assert "error" in result
        assert result["error"] == "API rate limit exceeded"

    @pytest.mark.asyncio
    async def test_get_income_statements_invalid_ticker(self) -> None:
        """Test income statement retrieval with invalid ticker."""
        result = await get_income_statements.ainvoke({"ticker": ""})
        
        assert "error" in result
        assert "Ticker cannot be empty" in result["error"]

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_cashflow_success(self, mock_request: AsyncMock, sample_financial_data: Dict[str, Any]) -> None:
        """Test successful cash flow statement retrieval."""
        mock_request.return_value = sample_financial_data["data"]
        
        result = await get_cashflow.ainvoke({"ticker": "AAPL", "period": "quarter", "limit": 3})
        
        assert result["ticker"] == "AAPL"
        assert result["period"] == "quarter"
        assert "data" in result

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_get_balance_sheet_success(self, mock_request: AsyncMock, sample_financial_data: Dict[str, Any]) -> None:
        """Test successful balance sheet retrieval."""
        mock_request.return_value = sample_financial_data["data"]
        
        result = await get_balance_sheet.ainvoke({"ticker": "MSFT"})
        
        assert result["ticker"] == "MSFT"
        assert result["period"] == "annual"  # default
        assert "data" in result


class TestFinnhub:
    """Test suite for Finnhub API integration."""

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.finnhub._make_finnhub_request')
    async def test_get_insider_sentiment_success(self, mock_request: AsyncMock) -> None:
        """Test successful insider sentiment retrieval."""
        mock_request.return_value = {
            "data": [{"symbol": "AAPL", "change": 100, "mspr": 0.8}]
        }
        
        result = await get_insiders_sentiment.ainvoke({"ticker": "AAPL", "days_back": 90})
        
        assert result["ticker"] == "AAPL"
        assert "data" in result

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.finnhub._get_finnhub_client')
    async def test_get_analyst_recommendations_success(self, mock_client: Mock) -> None:
        """Test successful analyst recommendations retrieval."""
        mock_finnhub = Mock()
        mock_finnhub.recommendation_trends.return_value = [
            {"symbol": "AAPL", "buy": 15, "hold": 5, "sell": 2, "strongBuy": 8}
        ]
        mock_client.return_value = mock_finnhub
        
        result = await get_analyst_recommendation.ainvoke({"ticker": "AAPL"})
        
        assert result["ticker"] == "AAPL"
        assert "recommendations" in result

    def test_finnhub_client_missing_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Finnhub client initialization with missing API key."""
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        
        from src.tools.data_providers.finnhub import _get_finnhub_client
        
        with pytest.raises(FinnhubError):
            _get_finnhub_client()


class TestAPIErrorHandling:
    """Test suite for API error handling across providers."""

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_rate_limit_handling(self, mock_request: AsyncMock) -> None:
        """Test handling of rate limit errors."""
        mock_request.return_value = {"error": "Rate limit exceeded"}
        
        result = await get_income_statements.ainvoke({"ticker": "AAPL"})
        
        assert "error" in result
        assert "Rate limit exceeded" in result["error"]

    @pytest.mark.asyncio
    @patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
    async def test_network_error_handling(self, mock_request: AsyncMock) -> None:
        """Test handling of network errors."""
        mock_request.return_value = {"error": "Unexpected error: Network error"}
        
        result = await get_income_statements.ainvoke({"ticker": "AAPL"})
        
        assert "error" in result
        assert "Unexpected error" in result["error"]
