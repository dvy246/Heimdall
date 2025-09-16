"""
Pytest configuration and shared fixtures for Heimdall test suite.

This module provides common test fixtures and configuration for the entire
test suite, including mock API clients, test data, and environment setup.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, Generator
from langchain_core.messages import HumanMessage, AIMessage

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["LOG_LEVEL"] = "DEBUG"

# Mock API keys for testing
TEST_API_KEYS = {
    "google": "test_google_key",
    "FINNHUB_API_KEY": "test_finnhub_key",
    "FPREP": "test_fmp_key",
    "Alpha_Vantage_Stock_API": "test_av_key",
    "polygon_api": "test_polygon_key",
    "SEC_API_KEY": "test_sec_key",
    "TAVILY_API_KEY": "test_tavily_key",
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for all tests."""
    for key, value in TEST_API_KEYS.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def sample_ticker() -> str:
    """Sample ticker symbol for testing."""
    return "AAPL"


@pytest.fixture
def sample_company_name() -> str:
    """Sample company name for testing."""
    return "Apple Inc."


@pytest.fixture
def sample_financial_data() -> Dict[str, Any]:
    """Sample financial data for testing API responses."""
    return {
        "ticker": "AAPL",
        "period": "annual",
        "data": [
            {
                "date": "2023-12-31",
                "revenue": 383285000000,
                "netIncome": 97000000000,
                "totalAssets": 352755000000,
                "totalDebt": 123000000000,
                "freeCashFlow": 84000000000
            }
        ]
    }


@pytest.fixture
def sample_news_data() -> Dict[str, Any]:
    """Sample news data for testing."""
    return {
        "articles": [
            {
                "title": "Apple Reports Strong Q4 Results",
                "description": "Apple Inc. reported better than expected earnings...",
                "url": "https://example.com/news/1",
                "publishedAt": "2023-12-01T10:00:00Z",
                "sentiment": "positive"
            }
        ]
    }


@pytest.fixture
def mock_langchain_model():
    """Mock LangChain model for testing."""
    mock_model = Mock()
    mock_model.invoke = AsyncMock(return_value=AIMessage(content="Test response"))
    mock_model.ainvoke = AsyncMock(return_value=AIMessage(content="Test async response"))
    return mock_model


@pytest.fixture
def sample_heimdall_state() -> Dict[str, Any]:
    """Sample Heimdall state for testing workflows."""
    return {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "mission_plan": "Analyze Apple's financial performance and market position",
        "messages": [
            HumanMessage(content="Analyze AAPL"),
            AIMessage(content="Starting analysis of Apple Inc.")
        ]
    }


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for API testing."""
    session = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"status": "success", "data": {}})
    session.get.return_value.__aenter__.return_value = response
    return session


@pytest.fixture
def mock_chromadb_client():
    """Mock ChromaDB client for testing RAG functionality."""
    mock_client = Mock()
    mock_collection = Mock()
    mock_collection.query.return_value = {
        "documents": [["Sample document content"]],
        "metadatas": [[{"source": "test.pdf"}]],
        "distances": [[0.1]]
    }
    mock_client.get_or_create_collection.return_value = mock_collection
    return mock_client


class MockAPIResponse:
    """Mock API response class for testing."""
    
    def __init__(self, data: Dict[str, Any], status_code: int = 200):
        self.data = data
        self.status_code = status_code
    
    async def json(self) -> Dict[str, Any]:
        return self.data
    
    @property
    def status(self) -> int:
        return self.status_code


@pytest.fixture
def mock_successful_api_response(sample_financial_data):
    """Mock successful API response."""
    return MockAPIResponse(sample_financial_data)


@pytest.fixture
def mock_error_api_response():
    """Mock error API response."""
    return MockAPIResponse({"error": "API rate limit exceeded"}, 429)


# Test data constants
SAMPLE_INCOME_STATEMENT = {
    "date": "2023-12-31",
    "revenue": 383285000000,
    "costOfRevenue": 214137000000,
    "grossProfit": 169148000000,
    "operatingIncome": 114301000000,
    "netIncome": 97000000000,
    "eps": 6.16
}

SAMPLE_BALANCE_SHEET = {
    "date": "2023-12-31",
    "totalAssets": 352755000000,
    "totalCurrentAssets": 143566000000,
    "totalNonCurrentAssets": 209189000000,
    "totalLiabilities": 255020000000,
    "totalEquity": 97735000000
}

SAMPLE_CASH_FLOW = {
    "date": "2023-12-31",
    "operatingCashFlow": 110543000000,
    "investingCashFlow": -3705000000,
    "financingCashFlow": -108488000000,
    "freeCashFlow": 84000000000
}
