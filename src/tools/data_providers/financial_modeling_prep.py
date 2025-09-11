"""
Financial Modeling Prep API tools for financial data retrieval.

This module provides tools for accessing Financial Modeling Prep API endpoints including
income statements, cash flow statements, and balance sheets with support for different
reporting periods and comprehensive data validation.
"""

import os
import json
import sys
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Literal, Union
from langchain_core.tools import tool
from src.config.logging_config import logger


class FMPError(Exception):
    """Custom exception for Financial Modeling Prep API errors."""
    pass


def _get_fmp_api_key() -> str:
    """
    Get the Financial Modeling Prep API key from environment variables.
    
    Returns:
        FMP API key
        
    Raises:
        FMPError: If API key is not found
    """
    api_key = os.getenv("FPREP")
    if not api_key:
        logger.error("FPREP API key not found in environment variables.")
        raise FMPError("FPREP API key is not set in environment variables.")
    
    return api_key


def _validate_ticker(ticker: str) -> str:
    """
    Validates ticker symbol format.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Validated ticker symbol
        
    Raises:
        ValueError: If ticker format is invalid
    """
    if not isinstance(ticker, str):
        raise ValueError("Ticker must be a string")
    
    ticker = ticker.upper().strip()
    
    if not ticker:
        raise ValueError("Ticker cannot be empty")
    
    if len(ticker) > 10:
        raise ValueError("Ticker symbol too long (max 10 characters)")
    
    # Allow alphanumeric characters, dots, and hyphens
    if not all(c.isalnum() or c in '.-' for c in ticker):
        raise ValueError("Ticker contains invalid characters")
    
    return ticker


def _validate_period(period: str) -> str:
    """
    Validates reporting period parameter.
    
    Args:
        period: Reporting period ('annual' or 'quarter')
        
    Returns:
        Validated period
        
    Raises:
        ValueError: If period is invalid
    """
    valid_periods = ['annual', 'quarter']
    if period not in valid_periods:
        raise ValueError(f"Period must be one of {valid_periods}, got: {period}")
    
    return period


async def _make_fmp_request(
    endpoint: str, 
    ticker: str,
    additional_params: Optional[Dict[str, Any]] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Any]:
    """
    Make an async request to Financial Modeling Prep API with error handling and rate limiting.
    
    Args:
        endpoint: API endpoint path
        ticker: Stock ticker symbol
        additional_params: Additional parameters for the API call
        session: Optional aiohttp session to reuse
        
    Returns:
        Dict containing API response data
        
    Raises:
        FMPError: If API key is missing or request fails
    """
    api_key = _get_fmp_api_key()
    base_url = "https://financialmodelingprep.com/api/v3"
    url = f"{base_url}/{endpoint}"
    
    params = {"symbol": ticker, "apikey": api_key}
    if additional_params:
        params.update(additional_params)
    
    logger.info(f"Making FMP API request to: {endpoint} for ticker: {ticker}")
    
    # Use provided session or create a new one
    if session:
        return await _execute_fmp_request(session, url, params, endpoint, ticker)
    else:
        async with aiohttp.ClientSession() as new_session:
            return await _execute_fmp_request(new_session, url, params, endpoint, ticker)


async def _execute_fmp_request(
    session: aiohttp.ClientSession, 
    url: str, 
    params: Dict[str, Any], 
    endpoint: str,
    ticker: str
) -> Dict[str, Any]:
    """Execute the HTTP request with retry logic."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data:
                        logger.warning(f"No data returned for {endpoint} (ticker: {ticker})")
                        return {"error": f"No data found for {ticker}"}
                    
                    if isinstance(data, dict) and "Error Message" in data:
                        error_msg = f"API error: {data['Error Message']}"
                        logger.error(error_msg)
                        return {"error": error_msg}
                    
                    logger.info(f"Successfully fetched data from FMP: {endpoint}")
                    return data
                    
                elif response.status == 429:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded for {endpoint} (attempt {attempt + 1})")
                    if attempt == max_retries - 1:
                        return {"error": "Rate limit exceeded. Please try again later."}
                    await asyncio.sleep(retry_delay * (attempt + 2))
                    
                elif response.status == 401:
                    logger.error(f"Unauthorized access to {endpoint}. Check API key.")
                    return {"error": "Unauthorized. Please check your API key."}
                    
                elif response.status == 404:
                    logger.warning(f"Data not found for {ticker} on {endpoint}")
                    return {"error": f"No data found for ticker {ticker}"}
                    
                else:
                    logger.error(f"HTTP error {response.status} for {endpoint}")
                    return {"error": f"HTTP status {response.status}"}
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed for {endpoint} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return {"error": f"Network request failed after {max_retries} attempts: {str(e)}"}
            await asyncio.sleep(retry_delay * (attempt + 1))
            
        except Exception as e:
            logger.critical(f"Unexpected error for {endpoint}: {e}", exc_info=True)
            return {"error": f"Unexpected error: {str(e)}"}
    
    return {"error": f"Failed to complete request for {endpoint} after {max_retries} attempts"}


@tool(description='Gets income statement data for a company')
async def get_income_statements(
    ticker: str, 
    period: Literal['annual', 'quarter'] = 'annual',
    limit: int = 5
) -> Dict[str, Any]:
    """
    Fetches the income statement of the specified company ticker.
    
    Args:
        ticker: The stock ticker symbol of the company
        period: The period for the income statement, either 'annual' or 'quarter'
        limit: Maximum number of periods to return (default: 5)
        
    Returns:
        Dict containing income statement data or error information
    """
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        period = _validate_period(period)
        
        if not isinstance(limit, int) or limit < 1 or limit > 40:
            limit = 5
            logger.warning(f"Invalid limit provided, using default: {limit}")
        
        additional_params = {"period": period, "limit": limit}
        data = await _make_fmp_request("income-statement", ticker, additional_params)
        
        if "error" in data:
            return data
        
        # Add metadata
        result = {
            "ticker": ticker,
            "period": period,
            "statements_count": len(data) if isinstance(data, list) else 1,
            "data": data
        }
        
        logger.info(f"Successfully fetched income statements for {ticker}")
        return result
        
    except (ValueError, FMPError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_income_statements: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description='Gets cash flow statement data for a company')
async def get_cashflow(
    ticker: str, 
    period: Literal['annual', 'quarter'] = 'annual',
    limit: int = 5
) -> Dict[str, Any]:
    """
    Fetches the cash flow statement of the specified company ticker.
    
    Args:
        ticker: The stock ticker symbol of the company
        period: The period for the cash flow statement, either 'annual' or 'quarter'
        limit: Maximum number of periods to return (default: 5)
        
    Returns:
        Dict containing cash flow statement data or error information
    """
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        period = _validate_period(period)
        
        if not isinstance(limit, int) or limit < 1 or limit > 40:
            limit = 5
            logger.warning(f"Invalid limit provided, using default: {limit}")
        
        additional_params = {"period": period, "limit": limit}
        data = await _make_fmp_request("cash-flow-statement", ticker, additional_params)
        
        if "error" in data:
            return data
        
        # Add metadata
        result = {
            "ticker": ticker,
            "period": period,
            "statements_count": len(data) if isinstance(data, list) else 1,
            "data": data
        }
        
        logger.info(f"Successfully fetched cash flow statements for {ticker}")
        return result
        
    except (ValueError, FMPError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_cashflow: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description='Gets balance sheet data for a company')
async def get_balance_sheet(
    ticker: str, 
    period: Literal['annual', 'quarter'] = 'annual',
    limit: int = 5
) -> Dict[str, Any]:
    """
    Fetches the balance sheet of the specified company ticker.
    
    Args:
        ticker: The stock ticker symbol of the company
        period: The period for the balance sheet, either 'annual' or 'quarter'
        limit: Maximum number of periods to return (default: 5)
        
    Returns:
        Dict containing balance sheet data or error information
    """
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        period = _validate_period(period)
        
        if not isinstance(limit, int) or limit < 1 or limit > 40:
            limit = 5
            logger.warning(f"Invalid limit provided, using default: {limit}")
        
        additional_params = {"period": period, "limit": limit}
        data = await _make_fmp_request("balance-sheet-statement", ticker, additional_params)
        
        if "error" in data:
            return data
        
        # Add metadata
        result = {
            "ticker": ticker,
            "period": period,
            "statements_count": len(data) if isinstance(data, list) else 1,
            "data": data
        }
        
        logger.info(f"Successfully fetched balance sheets for {ticker}")
        return result
        
    except (ValueError, FMPError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_balance_sheet: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description='Gets key financial metrics and ratios for a company')
async def get_key_metrics(
    ticker: str, 
    period: Literal['annual', 'quarter'] = 'annual',
    limit: int = 5
) -> Dict[str, Any]:
    """
    Fetches key financial metrics and ratios for the specified company ticker.
    
    Args:
        ticker: The stock ticker symbol of the company
        period: The period for the metrics, either 'annual' or 'quarter'
        limit: Maximum number of periods to return (default: 5)
        
    Returns:
        Dict containing key metrics data or error information
    """
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        period = _validate_period(period)
        
        if not isinstance(limit, int) or limit < 1 or limit > 40:
            limit = 5
            logger.warning(f"Invalid limit provided, using default: {limit}")
        
        additional_params = {"period": period, "limit": limit}
        data = await _make_fmp_request("key-metrics", ticker, additional_params)
        
        if "error" in data:
            return data
        
        # Add metadata
        result = {
            "ticker": ticker,
            "period": period,
            "metrics_count": len(data) if isinstance(data, list) else 1,
            "data": data
        }
        
        logger.info(f"Successfully fetched key metrics for {ticker}")
        return result
        
    except (ValueError, FMPError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_key_metrics: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description='Gets financial ratios for a company')
async def get_financial_ratios(
    ticker: str, 
    period: Literal['annual', 'quarter'] = 'annual',
    limit: int = 5
) -> Dict[str, Any]:
    """
    Fetches financial ratios for the specified company ticker.
    
    Args:
        ticker: The stock ticker symbol of the company
        period: The period for the ratios, either 'annual' or 'quarter'
        limit: Maximum number of periods to return (default: 5)
        
    Returns:
        Dict containing financial ratios data or error information
    """
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        period = _validate_period(period)
        
        if not isinstance(limit, int) or limit < 1 or limit > 40:
            limit = 5
            logger.warning(f"Invalid limit provided, using default: {limit}")
        
        additional_params = {"period": period, "limit": limit}
        data = await _make_fmp_request("ratios", ticker, additional_params)
        
        if "error" in data:
            return data
        
        # Add metadata
        result = {
            "ticker": ticker,
            "period": period,
            "ratios_count": len(data) if isinstance(data, list) else 1,
            "data": data
        }
        
        logger.info(f"Successfully fetched financial ratios for {ticker}")
        return result
        
    except (ValueError, FMPError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_financial_ratios: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}