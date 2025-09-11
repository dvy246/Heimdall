"""
Ticker Conversion Tools

This module provides tools for converting company names to ticker symbols
and validating ticker symbols.
"""

import aiohttp
from typing import Optional
from langchain_core.tools import tool
from src.config.logging_config import logger
from src.agents.preprocessing.preprocessing import pre_processing_agent


@tool("get_ticker_from_name")
async def get_ticker_from_name(company_name: str) -> str:
    """
    Asynchronously finds the ticker symbol for a company name using the Yahoo Finance search API.

    Args:
        company_name (str): The name of the company to search for.

    Returns:
        str: The ticker symbol if found, otherwise None.
    """
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    params = {"q": company_name, "quotes_count": 1, "country": "United States"}
    headers = {'User-Agent': user_agent}

    try:
        logger.info(f"Searching for ticker symbol for company: {company_name}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as res:
                res.raise_for_status()
                data = await res.json()

                if data and 'quotes' in data and data['quotes']:
                    first_quote = data['quotes'][0]
                    ticker = first_quote['symbol']
                    logger.info(f"Found ticker symbol: {ticker} for company: {company_name}")
                    return ticker
                else:
                    logger.warning(f"No ticker symbol found for company: {company_name}")
                    return None
                    
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error occurred while searching for ticker: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred while searching for ticker: {e}")
        return None


@tool("validate_ticker_symbol")
async def validate_ticker_symbol(ticker: str) -> bool:
    """
    Validates if a ticker symbol exists by checking Yahoo Finance.
    
    Args:
        ticker (str): The ticker symbol to validate
        
    Returns:
        bool: True if ticker exists, False otherwise
    """
    url = f"https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    params = {"q": ticker, "quotes_count": 1}
    headers = {'User-Agent': user_agent}

    try:
        logger.info(f"Validating ticker symbol: {ticker}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as res:
                res.raise_for_status()
                data = await res.json()

                if data and 'quotes' in data and data['quotes']:
                    # Check if the first result matches our ticker exactly
                    first_quote = data['quotes'][0]
                    found_ticker = first_quote['symbol']
                    is_valid = found_ticker.upper() == ticker.upper()
                    
                    logger.info(f"Ticker validation result for {ticker}: {is_valid}")
                    return is_valid
                else:
                    logger.warning(f"Ticker symbol not found: {ticker}")
                    return False
                    
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error occurred while validating ticker: {e}")
        return False
    except Exception as e:
        logger.error(f"An error occurred while validating ticker: {e}")
        return False

def convert_company_to_ticker(company_name: str) -> str:
    """
    Convenience function to convert a company name to ticker symbol.
    
    Args:
        company_name (str): The company name to convert
        
    Returns:
        str: The ticker symbol or "NOT_FOUND" if not found
    """
    try:
        # Log the start of the conversion process
        logger.info(f"Converting company name to ticker: {company_name}")
        
        # Use the preprocessing agent to get the ticker
        result = pre_processing_agent.invoke({
            "messages": [{"role": "user", "content": f"Find the ticker symbol for: {company_name}"}]
        })
        
        # Extract ticker from the response
        if hasattr(result, 'ticker'):
            ticker = result.ticker
        elif isinstance(result, dict) and 'ticker' in result:
            ticker = result['ticker']
        else:
            # Try to extract from messages if structured output failed
            messages = result.get('messages', [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    # Try to parse JSON from content
                    import json
                    try:
                        parsed = json.loads(content)
                        ticker = parsed.get('ticker', 'NOT_FOUND')
                    except:
                        ticker = 'NOT_FOUND'
                else:
                    ticker = 'NOT_FOUND'
            else:
                ticker = 'NOT_FOUND'
        
        logger.info(f"Ticker conversion result: {company_name} -> {ticker}")
        return ticker
        
    except Exception as e:
        logger.error(f"Error converting company name to ticker: {e}")
        return "NOT_FOUND"