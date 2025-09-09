import os
from datetime import datetime, timedelta
from typing import Dict, Any, Union, List
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from src.config.settings import model
from src.models.schemas import Sentiment
from src.config.logging_config import logger

@tool(description="Searches the web for a ticker and provides a sentiment analysis with a summary.")
async def analyze_news_sentiment(ticker: str, days_back: int = 30) -> Union[Dict[str, Any], str]:
    """
    Analyzes recent news sentiment for a given company ticker over a specified period.

    Args:
        ticker (str): The stock ticker symbol of the company.
        days_back (int): The number of days back to search for news. Defaults to 30.

    Returns:
        Union[Dict[str, Any], str]: A dictionary containing the sentiment analysis and summary,
                                    or an error message string.

    Raises:
        ValueError: If the TAVILY_API_KEY is not set.
    """
    logger.info(f"Analyzing news sentiment for ticker: {ticker} for the last {days_back} days.")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        logger.error("TAVILY_API_KEY not found in environment variables.")
        raise ValueError("TAVILY_API_KEY is not set in environment variables.")

    model_with_structure = model.with_structured_output(Sentiment)
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        search_query = f"{ticker} company news from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        tavily = TavilySearchResults(max_results=20, api_key=tavily_api_key)
        news_result = await tavily.ainvoke(search_query)

        if not news_result:
            logger.warning(f"No news articles found for {ticker} in the last {days_back} days.")
            return {"error": f"No articles found for {ticker} in the given period."}

        news_text = ""
        for i, result in enumerate(news_result[:10], 1):
            news_text += f"Article {i}: {result.get('title', 'No title')}\n"
            news_text += f"Content: {result.get('content', 'No content')[:200]}...\n\n"

    except Exception as e:
        logger.error(f"Error fetching news articles for {ticker}: {e}", exc_info=True)
        return {"error": f"Error fetching news articles: {str(e)}"}

    try:
        sentiment_result = await model_with_structure.ainvoke(news_text)
        prompt = f"Based on the sentiment analysis: {sentiment_result}, provide a detailed summary of the news sentiment."
        final_sentiment_with_reason = await model.ainvoke(prompt)
        logger.info(f"Successfully analyzed news sentiment for {ticker}.")
        return final_sentiment_with_reason
    except Exception as e:
        logger.error(f"Error during sentiment analysis for {ticker}: {e}", exc_info=True)
        return {"error": f"Error during sentiment analysis: {str(e)}"}

@tool(description='A tool to get current market news and trends.')
async def get_current_market_trends() -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Gets broad market trends for planning purposes using Tavily Search.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: A list of search results or an error message.

    Raises:
        ValueError: If the TAVILY_API_KEY is not set.
    """
    logger.info("Fetching current market trends.")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        logger.error("TAVILY_API_KEY not found in environment variables.")
        raise ValueError("TAVILY_API_KEY is not set in environment variables.")

    query = f"Current market trends for stocks as of {datetime.now().strftime('%Y-%m-%d')}"
    try:
        tavily = TavilySearchResults(max_results=20, api_key=tavily_api_key)
        trends = await tavily.ainvoke(query)
        if not trends:
            logger.warning("No current market trends found.")
            return {"message": "No current market trends found."}
        logger.info("Successfully fetched current market trends.")
        return trends
    except Exception as e:
        logger.error(f"Error fetching current market trends: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred while fetching market trends: {str(e)}"}
