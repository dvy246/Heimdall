from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchResults
from datetime import datetime
import os
from typing import List, Dict, Any
from src.config.logging_config import logger

# Import resilience utilities
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