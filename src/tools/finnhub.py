"""
Finnhub API tools for financial data retrieval.

This module provides tools for accessing Finnhub API endpoints including
insider sentiment, analyst recommendations, market status, company overviews,
and earnings surprises data.
"""

import os
import asyncio
import aiohttp
import finnhub
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from langchain_core.tools import tool
from finnhub import Client
from src.config.logging_config import logger


class FinnhubError(Exception):
    """Custom exception for Finnhub API errors."""
    pass


def _get_finnhub_client() -> Client:
    """
    Get a configured Finnhub client with API key validation.
    
    Returns:
        Configured Finnhub client
        
    Raises:
        FinnhubError: If API key is missing
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        logger.error("FINNHUB_API_KEY not found in environment variables.")
        raise FinnhubError("FINNHUB_API_KEY is not set in environment variables.")
    
    return Client(api_key=api_key)


async def _make_finnhub_request(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make an async HTTP request to Finnhub API with error handling and rate limiting.
    
    Args:
        url: API endpoint URL
        params: Request parameters
        
    Returns:
        Dict containing API response data
    """
    max_retries = 3
    retry_delay = 1
    
    logger.info(f"Making Finnhub API request to: {url}")
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if not data:
                        logger.warning(f"No data returned from Finnhub API")
                        return {"error": "No data returned from API"}
                    
                    logger.info("Successfully fetched data from Finnhub API")
                    return data
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return {"error": f"Network request failed after {max_retries} attempts: {str(e)}"}
            await asyncio.sleep(retry_delay * (attempt + 1))
            
        except Exception as e:
            logger.critical(f"Unexpected error in Finnhub request: {e}", exc_info=True)
            return {"error": f"Unexpected error: {str(e)}"}
    
    return {"error": f"Failed to complete request after {max_retries} attempts"}


@tool(description="Fetches insider sentiment data for a given stock ticker")
async def get_insiders_sentiment(ticker: str, days_back: int = 90) -> Dict[str, Any]:
    """
    Fetches insider sentiment data for a given stock ticker within a specified date range.
    
    Args:
        ticker: Stock symbol of the company
        days_back: Number of days to look back for sentiment data (default: 90)
        
    Returns:
        Dict containing insider sentiment data or error information
    """
    try:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            raise FinnhubError("FINNHUB_API_KEY is not set in environment variables.")

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        url = "https://finnhub.io/api/v1/stock/insider-sentiment"
        params = {
            "symbol": ticker,
            "from": start_date,
            "to": end_date,
            "token": api_key
        }

        sentiment_data = await _make_finnhub_request(url, params)
        
        if "error" in sentiment_data:
            return sentiment_data
        
        if not sentiment_data or 'data' not in sentiment_data:
            return {"message": f"No insider sentiment data found for {ticker} in the last {days_back} days."}
        
        # Calculate overall sentiment
        total_mspr = sum(item.get('mspr', 0) for item in sentiment_data['data'])
        sentiment_score = "Positive" if total_mspr > 0 else "Negative" if total_mspr < 0 else "Neutral"

        return {
            "ticker": ticker,
            "period_days": days_back,
            "monthly_sentiment_score_mspr": total_mspr,
            "overall_sentiment": sentiment_score,
            "data": sentiment_data['data']
        }

    except FinnhubError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_insiders_sentiment: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description="Gets analyst recommendations for a stock ticker")
async def get_analyst_recommendation(ticker: str) -> Dict[str, Any]:
    """
    Retrieves analyst recommendation trends for a specified ticker symbol from Finnhub API.
    
    Args:
        ticker: Stock symbol of the company
        
    Returns:
        Dict containing analyst recommendations or error information
    """
    try:
        client = _get_finnhub_client()
        
        logger.info(f"Fetching analyst recommendations for ticker: {ticker}")
        recommendations = client.recommendation_trends(ticker)
        
        if not recommendations:
            logger.warning(f"No analyst recommendation data found for ticker '{ticker}'.")
            return {"error": f"No analyst recommendation data found for ticker '{ticker}'."}
        
        logger.info(f"Successfully fetched analyst recommendations for {ticker}.")
        return {"ticker": ticker, "recommendations": recommendations}
        
    except FinnhubError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_analyst_recommendation: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description="Fetches the current market status for a given exchange")
def get_market_status(exchange: str = 'US') -> Dict[str, Any]:
    """
    Fetches the current market status for a given exchange using the Finnhub API.
    
    Args:
        exchange: The exchange to check (e.g., 'US', 'L'). Defaults to 'US'.
        
    Returns:
        Dict containing market status or error information
    """
    try:
        client = _get_finnhub_client()
        
        logger.info(f"Fetching market status for exchange: {exchange}")
        status = client.market_status(exchange=exchange)
        
        if not status:
            logger.warning(f"No market status found for exchange {exchange}.")
            return {"message": f"No market status found for exchange {exchange}."}
        
        logger.info(f"Successfully fetched market status for {exchange}.")
        return {"exchange": exchange, "status": status}
        
    except FinnhubError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_market_status: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description='Gets company overview from Finnhub')
async def get_company_overview(ticker: str) -> Dict[str, Any]:
    """
    Fetches a company overview for a specific ticker from Finnhub.io.
    
    Args:
        ticker: The ticker symbol to fetch the overview for (e.g., 'AAPL')
        
    Returns:
        Dict containing company overview data or error information
    """
    # Input validation
    if not isinstance(ticker, str) or not ticker.replace('.', '').replace('-', '').isalnum() or len(ticker) > 10:
        return {"error": "Invalid ticker symbol. Must be alphanumeric (with optional dots/hyphens) and up to 10 characters."}

    try:
        client = _get_finnhub_client()
        
        logger.info(f"Fetching company overview for ticker: {ticker}")
        company_overview = client.company_profile2(symbol=ticker)
        
        if not company_overview or not isinstance(company_overview, dict) or not company_overview.get("name"):
            logger.warning(f"No company overview found for ticker '{ticker}'.")
            return {"error": f"No company overview found for ticker '{ticker}'."}
        
        logger.info(f"Successfully fetched company overview for {ticker}.")
        return {"ticker": ticker, "overview": company_overview}
        
    except FinnhubError as e:
        return {"error": str(e)}
    except AttributeError as e:
        logger.error(f"Finnhub client error: {e}")
        return {"error": f"Finnhub client error: {str(e)}"}
    except Exception as e:
        logger.critical(f"Unexpected error in get_company_overview: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


@tool(description='Gets earnings surprises for the last 4 quarters')
async def get_earnings_surprises(ticker: str, sort_by_actual: bool = False) -> Dict[str, Any]:
    """
    Fetches the latest earnings surprises for a given stock ticker using the Finnhub API.
    
    Args:
        ticker: Stock symbol of the company
        sort_by_actual: If True, sorts by actual earnings in descending order
        
    Returns:
        Dict containing earnings surprises data or error information
    """
    try:
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            raise FinnhubError('FINNHUB_API_KEY environment variable not set')

        client = finnhub.Client(api_key=api_key)
        
        logger.info(f"Fetching earnings surprises for ticker: {ticker}")
        earnings = client.company_earnings(symbol=ticker, limit=5)
        
        if not earnings or not isinstance(earnings, list):
            logger.warning(f"No earnings data found for {ticker} or unexpected response format.")
            return {'error': 'No earnings data found or unexpected response format.'}
        
        if sort_by_actual:
            # Sort the list of earnings dicts by 'actual' in descending order
            earnings = sorted(earnings, key=lambda x: x.get('actual', 0), reverse=True)
        
        logger.info(f"Successfully fetched earnings surprises for {ticker}.")
        return {'ticker': ticker, 'earnings_surprises': earnings}
        
    except FinnhubError as e:
        return {'error': str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_earnings_surprises: {e}", exc_info=True)
        return {'error': f'Unexpected error: {str(e)}'}