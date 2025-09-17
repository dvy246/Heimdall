from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchResults
from datetime import datetime
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.tools.google_finance.tool import GoogleFinanceQueryRun
from langchain_community.utilities.google_finance import GoogleFinanceAPIWrapper    
import os
from typing import List, Dict, Any
from src.config.logging_config import logger
import asyncio
from src.tools.resilience.tool_recovery import retry_with_exponential_backoff, CircuitBreaker

# Circuit breakers for different tool categories
web_search_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

@tool(description="Returns the current date in YYYY-MM-DD format")
def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.now().strftime('%Y-%m-%d')

@retry_with_exponential_backoff(max_retries=2)
@web_search_breaker
@tool(description="Searches the web using Tavily API and returns top results")
async def search_web(query: str) -> List[Dict[str, Any]]:
    """
    Searches the web using Tavily API and returns top results.
    
    Args:
        query: Search query string
        
    Returns:
        List of search results containing title, url and snippet
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not found in environment variables")
        raise ValueError("TAVILY_API_KEY not set in environment variables")
        
    try:
        tavily = TavilySearchResults(max_results=20, api_key=api_key)
        return await tavily.ainvoke(query)
    except Exception as e:
        logger.error(f"Tavily search failed: {str(e)}")
        return []
        
@retry_with_exponential_backoff(max_retries=2)
@web_search_breaker
@tool(description="Searches the web using DuckDuckGo and returns top results") 
def search_web2(query: str) -> List[Dict[str, Any]]:
    """
    Searches the web using DuckDuckGo and returns top results.
    
    Args:
        query: Search query string
        
    Returns:
        List of search results containing title, url and snippet
    """
    try:
        return DuckDuckGoSearchResults(max_results=20).invoke(query)
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {str(e)}")
        return []
    
@retry_with_exponential_backoff(max_retries=2)
@web_search_breaker
@tool(description='uses google finance data to answer questions')
async def get_google_finance_data(query: str) -> str:
    """
    Asynchronously fetch Google Finance data for a given query.
    
    Args:
        query: The stock symbol or company name to search for

    Returns:
        The Google Finance data as a string
    """ 
    try:
        # Create the wrapper
        finance_wrapper = GoogleFinanceAPIWrapper()
        
        # Create the tool
        finance_tool = GoogleFinanceQueryRun(api_wrapper=finance_wrapper)
        
        # Run in thread pool since the tool is synchronous
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, finance_tool.run, query)
        
        return result
    except Exception as e:
        logger.error(f"Google Finance query failed for '{query}': {str(e)}")
        return f"Error fetching Google Finance data: {str(e)}"

@retry_with_exponential_backoff(max_retries=2)
@tool(description="Retrieve financial news from Yahoo Finance for a given ticker symbol")
async def get_yahoo_news(ticker_name: str) -> dict:
    """
    Retrieve financial news from Yahoo Finance for a given query.
    
    Args:
        ticker_name: Search term or company ticker symbol
        
    Returns:
        Dict containing news articles or error information
    """
    try:
        tool = YahooFinanceNewsTool()
        result = await tool.ainvoke(ticker_name)
        return {"data": result, "query": ticker_name}
    except Exception as e:
        return {"error": f"Failed to fetch Yahoo Finance news: {str(e)}", "query": ticker_name}