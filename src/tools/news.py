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

@tool(description="Gets global market status from Alpha Vantage.")
async def get_global_market_status() -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Fetches the global market status from Alpha Vantage API.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: A dictionary containing global market status or an error message.

    Raises:
        ValueError: If the Alpha Vantage API key is not set.
    """
    logger.info("Fetching global market status.")
    api_key = os.getenv('Alpha_Vantage_Stock_API')
    if not api_key:
        logger.error("Alpha_Vantage_Stock_API key not found in environment variables.")
        raise ValueError("Alpha_Vantage_Stock_API key is not set in environment variables.")
    
    url = "https://www.alphavantage.co/query"
    params = {'function': 'MARKET_STATUS', 'apikey': api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                if not data:
                    logger.warning("No global market status data found.")
                    return {"message": "No global market status data found."}
                logger.info("Successfully fetched global market status.")
                return data
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching global market status: {e}", exc_info=True)
        return {"error": f"Network or HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.critical(f"An unexpected error occurred fetching global market status: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}