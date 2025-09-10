"""
SEC API tools for financial filing retrieval.

This module provides tools for accessing SEC filing data including 10-K filings
with proper User-Agent handling and document parsing capabilities.
"""

import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from sec_api import QueryApi
from src.config.logging_config import logger


class SECError(Exception):
    """Custom exception for SEC API errors."""
    pass


def _get_user_agent() -> str:
    """
    Get the User-Agent string required by SEC API.
    
    Returns:
        User-Agent string
        
    Raises:
        SECError: If User-Agent is not configured
    """
    user_agent = os.getenv('EDGAR_USER_AGENT')
    if not user_agent:
        # Fallback to a default User-Agent if not set
        user_agent = 'Financial Analysis System contact@example.com'
        logger.warning("EDGAR_USER_AGENT not set, using default User-Agent")
    
    return user_agent


def _get_sec_api_key() -> str:
    """
    Get the SEC API key from environment variables.
    
    Returns:
        SEC API key
        
    Raises:
        SECError: If API key is not found
    """
    api_key = os.getenv('SEC_API_KEY')
    if not api_key:
        logger.error("SEC_API_KEY not found in environment variables.")
        raise SECError("SEC_API_KEY is not set in environment variables.")
    
    return api_key


def _validate_ticker(ticker: str) -> str:
    """
    Validates ticker symbol format for SEC API.
    
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
    
    # SEC tickers are typically alphanumeric
    if not ticker.replace('-', '').replace('.', '').isalnum():
        raise ValueError("Ticker contains invalid characters")
    
    return ticker


def _clean_html_content(html_content: str) -> str:
    """
    Clean and extract text from HTML content using BeautifulSoup.
    
    Args:
        html_content: Raw HTML content from SEC filing
        
    Returns:
        Cleaned plain text content
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean up whitespace
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        logger.error(f"Error cleaning HTML content: {e}")
        return html_content  # Return original content if cleaning fails


async def _fetch_filing_content(filing_url: str, user_agent: str) -> str:
    """
    Fetch the content of a SEC filing from the provided URL.
    
    Args:
        filing_url: URL to the SEC filing
        user_agent: User-Agent string for the request
        
    Returns:
        Plain text content of the filing
        
    Raises:
        SECError: If the request fails
    """
    headers = {'User-Agent': user_agent}
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(filing_url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        plain_text = _clean_html_content(html_content)
                        logger.info("Successfully fetched and parsed SEC filing content")
                        return plain_text
                    elif response.status == 429:
                        # Rate limit exceeded
                        logger.warning(f"Rate limit exceeded (attempt {attempt + 1})")
                        if attempt == max_retries - 1:
                            raise SECError("Rate limit exceeded. Please try again later.")
                        await asyncio.sleep(retry_delay * (attempt + 2))
                    else:
                        raise SECError(f"HTTP error {response.status} when fetching filing")
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise SECError(f"Network request failed after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(retry_delay * (attempt + 1))
            
        except Exception as e:
            logger.critical(f"Unexpected error fetching filing content: {e}", exc_info=True)
            raise SECError(f"Unexpected error: {str(e)}")
    
    raise SECError(f"Failed to fetch filing content after {max_retries} attempts")


@tool(description='Gets the latest 10-K filing for a company')
async def get_latest_10k_filing(ticker: str, include_amendments: bool = False) -> str:
    """
    Asynchronously fetches the full text of the most recent 10-K filing for a given company ticker.
    
    Args:
        ticker: The company's stock ticker (e.g., "TSLA")
        include_amendments: Whether to include 10-K/A amendment filings (default: False)
        
    Returns:
        The plain text content of the 10-K filing's primary document.
        Returns an error message if the filing cannot be fetched.
    """
    logger.info(f"Fetching latest 10-K filing for {ticker}")
    
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        api_key = _get_sec_api_key()
        user_agent = _get_user_agent()
        
        # Initialize QueryApi
        query_api = QueryApi(api_key=api_key)
        
        # Build query for 10-K filings
        form_types = ["10-K"]
        if include_amendments:
            form_types.append("10-K/A")
        
        form_query = " OR ".join([f'formType:"{form_type}"' for form_type in form_types])
        
        query = {
            "query": {"query_string": {"query": f'ticker:{ticker} AND ({form_query})'}},
            "from": 0,
            "size": 1,
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        
        logger.info(f"Executing SEC API query for {ticker}")
        response = query_api.get_filings(query=query)
        
        if not response or not response.get("filings"):
            error_msg = f"No 10-K filings found for ticker {ticker}"
            logger.warning(error_msg)
            return f"Error: {error_msg}"
        
        # Get the URL of the primary document from the latest filing
        filing = response["filings"][0]
        filing_url = filing.get("linkToHtml")
        
        if not filing_url:
            error_msg = f"Could not find a filing URL for {ticker}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        # Log filing information
        filed_at = filing.get("filedAt", "Unknown")
        form_type = filing.get("formType", "Unknown")
        logger.info(f"Found {form_type} filing for {ticker} filed at {filed_at}")
        
        # Fetch and parse the filing content
        plain_text = await _fetch_filing_content(filing_url, user_agent)
        
        # Add metadata to the beginning of the text
        metadata = f"""SEC Filing Information:
Ticker: {ticker}
Form Type: {form_type}
Filed At: {filed_at}
Filing URL: {filing_url}

--- FILING CONTENT ---

"""
        
        full_content = metadata + plain_text
        
        logger.info(f"Successfully fetched and parsed 10-K for {ticker}")
        return full_content
        
    except (ValueError, SECError) as e:
        error_msg = f"Error fetching SEC data for {ticker}: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error fetching SEC data for {ticker}: {str(e)}"
        logger.critical(error_msg, exc_info=True)
        return error_msg


@tool(description='Gets SEC filing metadata for a company')
async def get_filing_metadata(ticker: str, form_types: Optional[list] = None, limit: int = 5) -> Dict[str, Any]:
    """
    Retrieves metadata for SEC filings of a given company without downloading the full content.
    
    Args:
        ticker: The company's stock ticker
        form_types: List of form types to search for (default: ["10-K", "10-Q", "8-K"])
        limit: Maximum number of filings to return (default: 5)
        
    Returns:
        Dict containing filing metadata or error information
    """
    logger.info(f"Fetching SEC filing metadata for {ticker}")
    
    try:
        # Validate inputs
        ticker = _validate_ticker(ticker)
        api_key = _get_sec_api_key()
        
        if form_types is None:
            form_types = ["10-K", "10-Q", "8-K"]
        
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            limit = 5
            logger.warning(f"Invalid limit provided, using default: {limit}")
        
        # Initialize QueryApi
        query_api = QueryApi(api_key=api_key)
        
        # Build query
        form_query = " OR ".join([f'formType:"{form_type}"' for form_type in form_types])
        
        query = {
            "query": {"query_string": {"query": f'ticker:{ticker} AND ({form_query})'}},
            "from": 0,
            "size": limit,
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        
        logger.info(f"Executing SEC API metadata query for {ticker}")
        response = query_api.get_filings(query=query)
        
        if not response or not response.get("filings"):
            return {
                "ticker": ticker,
                "message": f"No filings found for ticker {ticker}",
                "filings": []
            }
        
        # Extract relevant metadata
        filings_metadata = []
        for filing in response["filings"]:
            metadata = {
                "formType": filing.get("formType"),
                "filedAt": filing.get("filedAt"),
                "acceptedDate": filing.get("acceptedDate"),
                "periodOfReport": filing.get("periodOfReport"),
                "companyName": filing.get("companyName"),
                "linkToHtml": filing.get("linkToHtml"),
                "linkToTxt": filing.get("linkToTxt"),
                "linkToXbrl": filing.get("linkToXbrl")
            }
            filings_metadata.append(metadata)
        
        result = {
            "ticker": ticker,
            "total_filings": len(filings_metadata),
            "filings": filings_metadata
        }
        
        logger.info(f"Successfully fetched metadata for {len(filings_metadata)} filings for {ticker}")
        return result
        
    except (ValueError, SECError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.critical(f"Unexpected error in get_filing_metadata: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}