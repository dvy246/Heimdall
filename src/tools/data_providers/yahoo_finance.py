from langchain_core.tools import tool
import yfinance as yf
from src.config.logging_config import logger


@tool(description='to get sustainability data')
def get_sustainability_data(ticker_symbol: str) -> str:
    """
    Retrieves environmental, social, and governance (ESG) sustainability metrics for a company.
    This tool provides sustainability scores and ratings that help assess a company's 
    environmental impact and social responsibility practices.
    
    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'MSFT')
        
    Returns:
        str: JSON representation of the sustainability data or None if no data available
    """
    try:
        logger.info(f"Fetching sustainability data for {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)
        sustainability_data = ticker.sustainability
        
        if sustainability_data is not None and not sustainability_data.empty:
            logger.info(f"Successfully retrieved sustainability data for {ticker_symbol}")
            return sustainability_data.to_json()
        else:
            logger.warning(f"No sustainability data available for {ticker_symbol}")
            return f"No sustainability data available for {ticker_symbol}"
    except Exception as e:
        logger.error(f"Error retrieving sustainability data for {ticker_symbol}: {e}")
        return f"Error retrieving sustainability data: {str(e)}"


@tool(description='to get major holders data')
def get_major_holders(ticker_symbol: str) -> str:
    """
    Fetches information about the largest shareholders of a company, including institutional
    investors and insider holdings. This data helps understand ownership structure and
    potential influence on company decisions.
    
    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'MSFT')
        
    Returns:
        str: JSON representation of the major holders data or error message
    """
    try:
        logger.info(f"Fetching major holders data for {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)
        major_holders = ticker.get_major_holders()
        
        if major_holders is not None and not major_holders.empty:
            logger.info(f"Successfully retrieved major holders data for {ticker_symbol}")
            return major_holders.to_json()
        else:
            logger.warning(f"No major holders data available for {ticker_symbol}")
            return f"No major holders data available for {ticker_symbol}"
    except Exception as e:
        logger.error(f"Error retrieving major holders data for {ticker_symbol}: {e}")
        return f"Error retrieving major holders data: {str(e)}"

@tool(description='to get financial statements data')
def get_financials(ticker_symbol: str) -> str:
    """
    Retrieves comprehensive financial statements including income statement, balance sheet,
    and cash flow data. This tool provides key financial metrics for fundamental analysis
    and company performance evaluation.
    
    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'MSFT', 'AAPL')
        
    Returns:
        str: JSON representation of financial statements data for the ticker
    """
    try:
        logger.info(f"Fetching financial statements for {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)
        financials = ticker.get_financials()
        if financials.empty:
            logger.warning(f"No financial data found for {ticker_symbol}")
            return f"No financial data found for {ticker_symbol}"
        logger.info(f"Successfully retrieved financial data for {ticker_symbol}")
        return financials.to_json()
    except Exception as e:
        logger.error(f"Error retrieving financial data for {ticker_symbol}: {e}")
        return f"Error retrieving financial data for {ticker_symbol}: {e}"


@tool(description='to fetch comprehensive financial analysis')
def fetch_company_analysis(ticker_symbol: str) -> dict:
    """
    Provides a comprehensive financial analysis package including analyst forecasts,
    ownership data, price targets, and recent news. This tool combines multiple
    data sources to give a holistic view of the company's financial outlook and
    market sentiment.
    
    Args:
        ticker_symbol (str): Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    
    Returns:
        dict: Dictionary containing growth estimates, major holders, price targets, and news
    """
    try:
        logger.info(f"Fetching comprehensive analysis for {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol.upper())
        
        growth_estimates = ticker.get_growth_estimates().to_json()
        major_holders = ticker.get_major_holders().to_json()
        analyst_price_targets = ticker.get_analyst_price_targets()
        news = ticker.get_news(count=2)
        
        logger.info(f"Successfully retrieved comprehensive analysis for {ticker_symbol}")
        return {
            'growth_estimates': growth_estimates,
            'major_holders': major_holders,
            'analyst_price_targets': analyst_price_targets,
            'news': news
        }
    except Exception as e:
        logger.error(f"Failed to retrieve data for {ticker_symbol}: {e}")
        raise ValueError(f"Failed to retrieve data for ticker '{ticker_symbol}': {str(e)}")