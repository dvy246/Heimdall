"""
Preprocessing Agents

This module contains agents responsible for preprocessing tasks such as
ticker symbol conversion and company name validation.
"""

from langgraph.graph.base import CompiledGraph
from langgraph.prebuilt import create_react_agent
from src.config.settings import model
from src.model_schemas.schemas import TickerResponse
from src.tools.search_sentiment import search_web, search_web2
from src.tools.ticker_conversion import get_ticker_from_name, validate_ticker_symbol, normalize_company_name
from src.config.logging_config import logger


# Ticker Conversion Agent
logger.info("Creating ticker conversion agent...")

pre_processing_agent: CompiledGraph = create_react_agent(
    model=model,
    tools=[search_web, search_web2, get_ticker_from_name, validate_ticker_symbol, normalize_company_name],
    name="pre_processing_agent",
    response_format=TickerResponse,
    prompt="""
You are a specialized assistant for ticker symbol extraction and validation. Your sole task is to extract the official stock ticker symbol for a given company name.

**Objective:** Convert company names to their official stock ticker symbols with high accuracy and reliability.

**Methodology:**
1. **Name Normalization:** Use `normalize_company_name` to clean and standardize the company name
2. **Direct Ticker Search:** Use `get_ticker_from_name` to search Yahoo Finance for the ticker symbol
3. **Web Search Validation:** Use `search_web` and `search_web2` to cross-validate ticker symbols from multiple sources
4. **Ticker Validation:** Use `validate_ticker_symbol` to confirm the ticker exists and is active
5. **Final Verification:** Ensure the ticker matches the correct company through additional web searches

**Search Strategy:**
- Search for "[company name] stock ticker symbol NYSE NASDAQ"
- Look for official company websites, financial news, and stock exchange listings
- Cross-reference multiple sources to ensure accuracy
- Pay attention to exchange suffixes (e.g., .NS for NSE, .L for LSE)

**Quality Assurance:**
- Verify the ticker symbol corresponds to the correct company
- Check for common variations and ensure you have the primary listing
- Validate against major exchanges (NYSE, NASDAQ, etc.)
- Handle international companies with appropriate exchange suffixes

**Output Requirements:**
- Return ONLY the ticker symbol in the specified JSON format: {"ticker": "TICKER_SYMBOL"}
- If no valid ticker is found after thorough search, return {"ticker": "NOT_FOUND"}
- Do not include explanations, commentary, or additional information

**Error Handling:**
- If search tools fail, try alternative search strategies
- If multiple tickers are found, select the primary/most liquid listing
- Handle edge cases like recently IPO'd companies or delisted stocks

**Examples:**
- Microsoft Corporation → {"ticker": "MSFT"}
- Apple Inc. → {"ticker": "AAPL"}
- HDFC Bank Limited → {"ticker": "HDFCBANK.NS"}
- Alphabet Inc. → {"ticker": "GOOGL"}

Remember: Accuracy is paramount. Take time to validate your results through multiple sources.
"""
)

logger.info("Ticker conversion agent created successfully.")


def convert_company_to_ticker(company_name: str) -> str:
    """
    Convenience function to convert a company name to ticker symbol.
    
    Args:
        company_name (str): The company name to convert
        
    Returns:
        str: The ticker symbol or "NOT_FOUND" if not found
    """
    try:
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


def validate_company_ticker_pair(company_name: str, ticker: str) -> bool:
    """
    Validates that a ticker symbol corresponds to the given company name.
    
    Args:
        company_name (str): The company name
        ticker (str): The ticker symbol to validate
        
    Returns:
        bool: True if the ticker matches the company, False otherwise
    """
    try:
        logger.info(f"Validating company-ticker pair: {company_name} <-> {ticker}")
        
        # First validate that the ticker exists
        import asyncio
        is_valid_ticker = asyncio.run(validate_ticker_symbol(ticker))
        
        if not is_valid_ticker:
            logger.warning(f"Ticker {ticker} is not valid")
            return False
        
        # Then check if the ticker matches the company name
        found_ticker = convert_company_to_ticker(company_name)
        
        # Compare tickers (case insensitive)
        matches = found_ticker.upper() == ticker.upper()
        
        logger.info(f"Company-ticker validation result: {matches}")
        return matches
        
    except Exception as e:
        logger.error(f"Error validating company-ticker pair: {e}")
        return False