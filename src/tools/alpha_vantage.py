"""
Alpha Vantage API tools for financial data retrieval.

This module provides tools for accessing Alpha Vantage API endpoints including
company overviews, insider information, financial statements, earnings data,
economic indicators, and market status information.
"""

import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Literal
from langchain_core.tools import tool
from src.config.looging_config import logger


class AlphaVantageError(Exception):
    """Custom exception for Alpha Vantage API errors."""
    pass


async def _make_alpha_vantage_request(
    function: str, 
    symbol: Optional[str] = None, 
    additional_params: Optional[Dict[str, Any]] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Any]:
    """
    Make an async request to Alpha Vantage API with error handling and rate limiting.
    
    Args:
        function: Alpha Vantage API function name
        symbol: Stock symbol (optional)
        additional_params: Additional parameters for the API call
        session: Optional aiohttp session to reuse
        
    Returns:
        Dict containing API response data
        
    Raises:
        AlphaVantageError: If API key is missing or request fails
    """
    api_key = os.getenv('Alpha_Vantage_Stock_API')
    if not api_key:
        logger.error("Alpha_Vantage_Stock_API key not found in environment variables.")
        raise AlphaVantageError("Alpha_Vantage_Stock_API key is not set in environment variables.")
    
    url = 'https://www.alphavantage.co/query'
    params = {'function': function, 'apikey': api_key}
    
    if symbol:
        params['symbol'] = symbol
    
    if additional_params:
        params.update(additional_params)
    
    logger.info(f"Making Alpha Vantage API request: {function} for symbol: {symbol}")
    
    # Use provided session or create a new one
    if session:
        return await _execute_request(session, url, params, function, symbol)
    else:
        async with aiohttp.ClientSession() as new_session:
            return await _execute_request(new_session, url, params, function, symbol)


async def _execute_request(
    session: aiohttp.ClientSession, 
    url: str, 
    params: Dict[str, Any], 
    function: str, 
    symbol: Optional[str]
) -> Dict[str, Any]:
    """Execute the HTTP request with retry logic."""
    max_retries = 4
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Check for API-specific errors
                if "Note" in data:
                    error_msg = f"API limit reached for {function}"
                    if symbol:
                        error_msg += f" (symbol: {symbol})"
                    logger.warning(error_msg)
                    return {"error": error_msg}
                
                if "Error Message" in data:
                    error_msg = f"API error: {data['Error Message']}"
                    logger.error(error_msg)
                    return {"error": error_msg}
                
                if not data:
                    error_msg = f"No data returned for {function}"
                    if symbol:
                        error_msg += f" (symbol: {symbol})"
                    logger.warning(error_msg)
                    return {"error": error_msg}
                
                logger.info(f"Successfully fetched data for {function}")
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed for {function} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return {"error": f"Network request failed after {max_retries} attempts: {str(e)}"}
            await asyncio.sleep(retry_delay * (attempt + 1))
            
        except Exception as e:
            logger.critical(f"Unexpected error for {function}: {e}", exc_info=True)
            return {"error": f"Unexpected error: {str(e)}"}
    
    return {"error": f"Failed to complete request for {function} after {max_retries} attempts"}


@tool(description='get company overview')
async def company_overview(ticker: str) -> Dict[str, Any]:
    """
    Retrieves detailed company information including financial metrics,
    business description, and key statistics from Alpha Vantage API.
    
    Args:
        ticker: Stock symbol of the company (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Dict containing company overview data or error information
    """
    try:
        return await _make_alpha_vantage_request('OVERVIEW', ticker)
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Gets insider information and transactions for a company')
async def get_insider_info(ticker: str) -> Dict[str, Any]:
    """
    Returns the latest and historical insider transactions made by key stakeholders 
    (e.g., founders, executives, board members, etc.) of a specific company.
    
    Args:
        ticker: Stock symbol of the company
        
    Returns:
        Dict containing insider transaction data or error information
    """
    try:
        return await _make_alpha_vantage_request('INSIDER_TRANSACTIONS', ticker)
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Gets balance sheet data for a company')
async def get_balance_sheet(ticker: str, period: Literal['annual', 'quarterly'] = 'annual') -> Dict[str, Any]:
    """
    Retrieves balance sheet data for a specified company.
    
    Args:
        ticker: Stock symbol of the company
        period: Reporting period - 'annual' or 'quarterly'
        
    Returns:
        Dict containing balance sheet data or error information
    """
    try:
        additional_params = {}
        if period == 'quarterly':
            additional_params['datatype'] = 'json'
            
        return await _make_alpha_vantage_request('BALANCE_SHEET', ticker, additional_params)
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Gets earnings data for a company')
async def get_earnings(ticker: str) -> Dict[str, Any]:
    """
    Retrieves quarterly and annual earnings data for a specified company.
    
    Args:
        ticker: Stock symbol of the company
        
    Returns:
        Dict containing earnings data or error information
    """
    try:
        return await _make_alpha_vantage_request('EARNINGS', ticker)
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Performs advanced analytics on company data')
async def advanced_analyst(
    ticker: str,
    interval: str = 'daily',
    window_size: int = 50,
    calculations: List[str] = None,
    range_period: str = '6month',
    ohlc: str = "close"
) -> Dict[str, Any]:
    """
    Returns a rich set of advanced analytics metrics (e.g., total return, variance, 
    auto-correlation, etc.) for a given time series over sliding time windows.
    
    Args:
        ticker: Stock symbol of the company
        interval: Time interval for data points
        window_size: Size of the sliding window
        calculations: List of calculations to perform
        range_period: Time range for analysis
        ohlc: OHLC field to analyze
        
    Returns:
        Dict containing advanced analytics data or error information
    """
    if calculations is None:
        calculations = ['MEAN', 'STDDEV', 'VARIANCE']
    
    try:
        additional_params = {
            'SYMBOLS': ticker,
            'RANGE': range_period,
            'INTERVAL': interval,
            'WINDOW_SIZE': window_size,
            'CALCULATIONS': ','.join(calculations),
            'OHLC': ohlc
        }
        
        data = await _make_alpha_vantage_request('ANALYTICS_SLIDING_WINDOW', None, additional_params)
        return data.get("payload", data) if "payload" in data else data
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Gets economic indicators data')
async def get_economic_indicators(
    indicators: List[str] = None, 
    limit_per_indicator: int = 5
) -> Dict[str, Any]:
    """
    Fetches economic indicators from Alpha Vantage API.
    
    Args:
        indicators: List of economic indicators to fetch
        limit_per_indicator: Maximum number of data points per indicator
        
    Returns:
        Dict containing economic indicators data or error information
    """
    valid_indicators = [
        "REAL_GDP", "REAL_GDP_PER_CAPITA", "TREASURY_YIELD", "FEDERAL_FUNDS_RATE",
        "CPI", "INFLATION", "RETAIL_SALES", "DURABLES", "UNEMPLOYMENT", "NONFARM_PAYROLL"
    ]
    
    if indicators is None:
        indicators = valid_indicators[:3]  # Default to first 3 indicators
    
    results = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            for indicator in indicators:
                if indicator not in valid_indicators:
                    results[indicator] = {"error": f"Invalid indicator: {indicator}"}
                    continue
                
                try:
                    data = await _make_alpha_vantage_request(indicator, None, None, session)
                    if 'data' in data:
                        # Sort by date and limit results
                        sorted_data = sorted(data['data'], key=lambda x: x['date'], reverse=True)
                        results[indicator] = sorted_data[:limit_per_indicator]
                    else:
                        results[indicator] = data
                    
                    # Rate limiting between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    results[indicator] = {"error": f"Failed to fetch {indicator}: {str(e)}"}
        
        return results
    except Exception as e:
        return {'error': f'Failed to fetch economic indicators: {str(e)}'}


@tool(description='Gets global market status information')
async def get_global_market_status() -> Dict[str, Any]:
    """
    Fetches the global market status from Alpha Vantage API.
    
    Returns:
        Dict containing global market status or error information
    """
    try:
        data=await _make_alpha_vantage_request('MARKET_STATUS')
        return data
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Gets shares outstanding data for a company')
async def get_shares_outstanding(symbol: str) -> Dict[str, Any]:
    """
    Fetches shares outstanding data for a given stock symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dict containing shares outstanding data or error information
    """
    try:
        data = await _make_alpha_vantage_request('SHARES_OUTSTANDING', symbol)
        return {"symbol": symbol, "data": data}
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Gets corporate actions data for a company')
async def get_corporate_actions(symbol: str) -> Dict[str, Any]:
    """
    Fetches corporate actions (specifically dividend events) for a given stock symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dict containing corporate actions data or error information
    """
    try:
        data = await _make_alpha_vantage_request('DIVIDENDS', symbol)
        return {"symbol": symbol, "data": data}
    except AlphaVantageError as e:
        return {'error': str(e)}


@tool(description='Gets stock splits data for a company')
async def get_stock_splits(symbol: str) -> Dict[str, Any]:
    """
    Fetches stock split events for a given stock symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dict containing stock splits data or error information
    """
    try:
        data = await _make_alpha_vantage_request('SPLITS', symbol)
        return {"symbol": symbol, "data": data}
    except AlphaVantageError as e:
        return {'error': str(e)}