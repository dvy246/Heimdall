import os
import aiohttp
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from typing import Dict, Any, Union
from langchain_core.tools import tool
from finnhub import Client
from src.config.logging_config import logger
from src.tools.resilience.tool_recovery import retry_with_exponential_backoff,CircuitBreaker

market_status_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)


@retry_with_exponential_backoff(max_retries=5)
@market_status_breaker
@tool(description="Fetches the current market status for a given exchange using the Finnhub API.")
def get_market_status(exchange: str = 'US') -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Fetches the current market status for a given exchange using the Finnhub API.

    Args:
        exchange (str): The exchange to check (e.g., 'US', 'L'). Defaults to 'US'.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: A dictionary containing market status or an error message.

    Raises:
        ValueError: If the Finnhub API key is not set.
    """
    logger.info(f"Fetching market status for exchange: {exchange}")
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        logger.error("FINNHUB_API_KEY not found in environment variables.")
        raise ValueError("FINNHUB_API_KEY is not set in environment variables.")

    try:
        finnhub_client = Client(api_key=api_key)
        status = finnhub_client.market_status(exchange=exchange)
        if not status:
            logger.warning(f"No market status found for exchange {exchange}.")
            return {"message": f"No market status found for exchange {exchange}."}
        logger.info(f"Successfully fetched market status for {exchange}.")
        return status
    except Exception as e:
        logger.critical(f"An unexpected error occurred fetching market status for {exchange}: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

def extract_regions(world: dict) -> list:
    """
    Extracts the list of region names from the 'markets' key in the provided dictionary.

    Args:
        world (dict): The dictionary containing market data.

    Returns:
        list: A list of region names, or an empty list if not found.
    """
    regions = []
    markets = world.get('markets', [])
    for market in markets:
        region = market.get('region')
        if region:
            regions.append(region)
    return regions


@retry_with_exponential_backoff(max_retries=5)
@market_status_breaker
@tool("to get_global_market_status")
async def get_global_market_status() -> dict:
    """
    Fetches the global market status from Alpha Vantage.

    Returns:
        dict: The market status data, including a list of regions, or an error message if the request fails.
    """
    api_key = os.getenv('Alpha_Vantage_Stock_API')
    if not api_key:
        return {"error": "Alpha Vantage API key is missing. Please set the Alpha_Vantage_Stock_API environment variable."}
    url = "https://www.alphavantage.co/query"
    params = {'function': 'MARKET_STATUS', 'apikey': api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    regions = extract_regions(data)
                    return {"data": data, "regions": regions}
                else:
                    return {"error": f"HTTP status {response.status}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def get_insights(ticker:str,news_data):
    for article in news_data.get('results', []):
        if isinstance(article, dict):
            insights = article.get('insights', [])
            description = article.get('description', '[]')
            for insight in insights:
                if isinstance(insight, dict) and insight.get('ticker') == ticker:
                    return {'insight': insight, 'description': description}
@retry_with_exponential_backoff(max_retries=5)
@market_status_breaker
@tool(description='gets the news sentiments with reason')
async def get_latest_news_sentiments(ticker: str) -> Dict[str, Any]:
    """
    Fetches the latest news sentiments for a given stock ticker using the Polygon.io API.

    Args:
        ticker (str): The stock ticker symbol for which to retrieve news sentiments.

    Returns:
        Dict[str, Any]: A dictionary containing news insights with sentiment and reasoning,
                        or an error message if the request fails or the API key is missing.

    Raises:
        Returns an error dictionary if the HTTP request fails or an unexpected exception occurs.
    """
    api = os.getenv('polygon_api')
    if not api:
        return {'error': 'polygon_api environment variable not set'}
    url = 'https://api.polygon.io/v2/reference/news'
    params = {
        'apikey': api,
        'ticker': ticker
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as news_response:
                if news_response.status == 200:
                    news_data = await news_response.json()
                    news_insights = get_insights(ticker, news_data)
                    return news_insights
                else:
                    return {'error': f'Failed to fetch news: HTTP {news_response.status}'}
    except aiohttp.ClientError as e:
        return {'error': f'HTTP request failed: {e}'}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {e}'}

@retry_with_exponential_backoff(max_retries=5)
@market_status_breaker
@tool(description='a tool to get current news')
async def get_current_markettrends():
    """Get broad market trends for planning."""
    from src.tools.utilities.extra import search_web
    query = f"Current market trends for stocks as of {datetime.now().strftime('%Y-%m-%d')}"
    return await search_web(query)