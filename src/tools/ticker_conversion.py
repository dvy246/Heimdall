"""
Ticker Conversion Tools

This module provides tools for converting company names to ticker symbols
and validating ticker symbols.
"""

import aiohttp
from typing import Optional
from langchain_core.tools import tool
from src.config.logging_config import logger


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


@tool("normalize_company_name")
def normalize_company_name(company_name: str) -> str:
    """
    Normalizes a company name for better ticker search results.
    
    Args:
        company_name (str): The company name to normalize
        
    Returns:
        str: Normalized company name
    """
    try:
        # Remove common suffixes and normalize
        suffixes_to_remove = [
            'Inc.', 'Inc', 'Corporation', 'Corp.', 'Corp', 'Company', 'Co.', 'Co',
            'Limited', 'Ltd.', 'Ltd', 'LLC', 'L.L.C.', 'LP', 'L.P.',
            'PLC', 'P.L.C.', 'AG', 'SA', 'NV', 'BV'
        ]
        
        normalized = company_name.strip()
        
        # Remove suffixes (case insensitive)
        for suffix in suffixes_to_remove:
            if normalized.upper().endswith(suffix.upper()):
                normalized = normalized[:-len(suffix)].strip()
                break
        
        # Remove extra whitespace and normalize
        normalized = ' '.join(normalized.split())
        
        logger.info(f"Normalized company name: '{company_name}' -> '{normalized}'")
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing company name '{company_name}': {e}")
        return company_name