"""
Polygon.io API tools for financial data retrieval.

This module provides tools for accessing Polygon.io API endpoints including
ticker overviews and latest news sentiments.
"""

import os
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, Union
from langchain_core.tools import tool
from src.config.looging_config import logger


class PolygonError(Exception):
    """Custom exception for Polygon.io API errors."""
    pass


def _validate_date(date: str) -> str:
    """
    Validates if a given string is in 'YYYY-MM-DD' format.
    
    Args:
        date: The date string to validate
        
    Returns:
        The validated date string
        
    Raises:
        ValueError: If the date is not in the correct format
    """
    try:
        return datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format received: {date}. Expected YYYY-MM-DD.")
        raise ValueError(f"Invalid date: {date}. Must be YYYY-MM-DD format.")


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


async def _make_polygon_request(
    endpoint: str, 
    params: Optional[Dict[str, Any]] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Any]:
    """
    Make an async request to Polygon.io API with error handling and rate limiting.
    
    Args:
        endpoint: API endpoint path
        params: Additional parameters for the API call
        session: Optional aiohttp session to reuse
        
    Returns:
        Dict containing API response data
        
    Raises:
        PolygonError: If API key is missing or request fails
    """
    api_key = os.getenv('polygon_api')
    if not api_key:
        logger.error("polygon_api key not found in environment variables.")
        raise PolygonError("polygon_api key is not set in environment variables.")
    
    base_url = "https://api.polygon.io"
    url = f"{base_url}{endpoint}"
    
    request_params = {"apiKey": api_key}
    if params:
        request_params.update(params)
    
    logger.info(f"Making Polygon.io API request to: {endpoint}")
    
    # Use provided session or create a new one
    if session:
        return await _execute_polygon_request(session, url, request_params, endpoint)
    else:
        async with aiohttp.ClientSession() as new_session:
            return await _execute_polygon_request(new_session, url, request_params, endpoint)


async def _execute_polygon_request(
    session: aiohttp.ClientSession, 
    url: str, 
    params: Dict[str, Any], 
    endpoint: str
) -> Dict[str, Any]:
    """Execute the HTTP request with retry logic."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched data from Polygon.io: {endpoint}")
                    return data
                elif response.status == 429:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded for {endpoint} (attempt {attempt + 1})")
                    if attempt == max_retries - 1:
                        return {"error": "Rate limit exceeded. Please try again later."}
                    await asyncio.sleep(retry_delay * (attempt + 2))  # Longer delay for rate limits
                elif response.status == 401:
                    logger.error(f"Unauthorized access to {endpoint}. Check API key.")
                    return {"error": "Unauthorized. Please check your API key."}
                elif response.status == 404:
                    logger.warning(f"Resource not found for {endpoint}")
                    return {"error": "Resource not found."}
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


@tool(description="Gets ticker overview from Polygon.io")
async def get_ticker_overview(ticker: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches an overview for a specific ticker from Polygon.io.
    
    Args:
        ticker: The ticker symbol to fetch the overview for (e.g., 'AAPL')
        date: Optional date for which to fetch the overview in 'YYYY-MM-DD' format.
              If not provided, the latest available data is returned.
              
    Returns:
        Dict containing ticker overview data or error information
    """
    try:
        # Validate ticker
        ticker = _validate_ticker(ticker)
        
        # Validate date if provided
        params = {}
        if date:
            validated_date = _validate_date(date)
            params["date"] = validated_date
        
        endpoint = f"/v3/reference/tickers/{ticker}"
        data = await _make_polygon_request(endpoint, params)
        
        if "error" in data:
            return data
        
        # Add ticker to response for consistency
        if "results" in data:
            data["ticker"] = ticker
        
        return data
        
    except (ValueError, PolygonError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_ticker_overview: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def _extract_insights(ticker: str, news_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract insights from news data for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
        news_data: News data from Polygon.io API
        
    Returns:
        Dict containing extracted insights
    """
    insights_list = []
    
    try:
        results = news_data.get('results', [])
        
        for article in results:
            if not isinstance(article, dict):
                continue
                
            article_insights = article.get('insights', [])
            description = article.get('description', '')
            title = article.get('title', '')
            published_utc = article.get('published_utc', '')
            
            for insight in article_insights:
                if isinstance(insight, dict) and insight.get('ticker') == ticker:
                    insight_data = {
                        'ticker': ticker,
                        'insight': insight,
                        'description': description,
                        'title': title,
                        'published_utc': published_utc
                    }
                    insights_list.append(insight_data)
        
        return {
            'ticker': ticker,
            'total_insights': len(insights_list),
            'insights': insights_list
        }
        
    except Exception as e:
        logger.error(f"Error extracting insights for {ticker}: {e}")
        return {
            'ticker': ticker,
            'error': f'Error extracting insights: {str(e)}',
            'insights': []
        }


@tool(description='Gets the latest news sentiments for a ticker')
async def get_latest_news_sentiments(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    Fetches the latest news sentiments for a given stock ticker using the Polygon.io API.
    
    Args:
        ticker: Stock ticker symbol for which to retrieve news sentiments
        limit: Maximum number of news articles to retrieve (default: 10)
        
    Returns:
        Dict containing news insights with sentiment and reasoning, or error information
    """
    try:
        # Validate ticker
        ticker = _validate_ticker(ticker)
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            limit = 10
            logger.warning(f"Invalid limit provided, using default: {limit}")
        
        endpoint = "/v2/reference/news"
        params = {
            'ticker': ticker,
            'limit': limit,
            'sort': 'published_utc',
            'order': 'desc'
        }
        
        news_data = await _make_polygon_request(endpoint, params)
        
        if "error" in news_data:
            return news_data
        
        if not news_data or 'results' not in news_data:
            return {
                'ticker': ticker,
                'message': f'No news data found for {ticker}',
                'insights': []
            }
        
        # Extract insights from news data
        insights = _extract_insights(ticker, news_data)
        
        # Add additional metadata
        insights['total_articles'] = len(news_data.get('results', []))
        insights['request_limit'] = limit
        
        logger.info(f"Successfully fetched news sentiments for {ticker}")
        return insights
        
    except (ValueError, PolygonError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_latest_news_sentiments: {e}", exc_info=True)
        return {'error': f'Unexpected error: {str(e)}'}