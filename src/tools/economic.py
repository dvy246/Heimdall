import os
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Union
from langchain_core.tools import tool
from src.config.settings import model
from src.models.schemas import Sector
from src.config.logging_config import logger

VALID_INDICATORS: Dict[str, str] = {
    "REAL_GDP": "Real GDP Trending",
    "REAL_GDP_PER_CAPITA": "Real GDP per Capita",
    "TREASURY_YIELD": "Treasury Yield Trending",
    "FEDERAL_FUNDS_RATE": "Federal Funds (Interest) Rate",
    "CPI": "CPI",
    "INFLATION": "Inflation",
    "RETAIL_SALES": "Retail Sales",
    "DURABLES": "Durable Goods Orders",
    "UNEMPLOYMENT": "Unemployment Rate",
    "NONFARM_PAYROLL": "Nonfarm Payroll"
}

VALID_SECTORS: set[str] = {
    "Energy", "Technology", "Healthcare", "Financial Services", "Consumer Cyclical",
    "Consumer Defensive", "Industrials", "Basic Materials", "Real Estate", "Utilities",
    "Communication Services",
}

def validate_date(date: str) -> str:
    """
    Validates if a given string is in 'YYYY-MM-DD' format.

    Args:
        date (str): The date string to validate.

    Returns:
        str: The validated date string.

    Raises:
        ValueError: If the date is not in the correct format.
    """
    try:
        return datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format received: {date}. Expected YYYY-MM-DD.")
        raise ValueError(f"Invalid date: {date}. Must be YYYY-MM-DD format.")

@tool(description='A tool to get economic indicators from Alpha Vantage.')
async def get_economic_indicators(indicators: List[str] = list(VALID_INDICATORS.keys()), limit: int = 5) -> Dict[str, Any]:
    """
    Fetches economic indicators from the Alpha Vantage API.

    Args:
        indicators (List[str]): A list of economic indicators to fetch. Defaults to all valid indicators.
        limit (int): The maximum number of data points to return for each indicator.

    Returns:
        Dict[str, Any]: A dictionary where keys are indicator names and values are lists of data points
                        or an error message.
    """
    logger.info(f"Fetching economic indicators: {indicators} with limit {limit}")
    api_key = os.getenv('Alpha_Vantage_Stock_API')
    if not api_key:
        logger.error("Alpha_Vantage_Stock_API key not found in environment variables.")
        raise ValueError("Alpha_Vantage_Stock_API key is not set in environment variables.")

    results: Dict[str, Any] = {}
    async with aiohttp.ClientSession() as session:
        for indicator in indicators:
            if indicator not in VALID_INDICATORS:
                logger.warning(f"Attempted to fetch invalid indicator: {indicator}")
                results[indicator] = "Invalid indicator name"
                continue
            
            params = {'function': indicator, 'apikey': api_key}
            url = 'https://www.alphavantage.co/query'
            
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if 'data' in data:
                        sorted_data = sorted(data['data'], key=lambda x: x['date'], reverse=True)
                        results[indicator] = sorted_data[:limit]
                        logger.info(f"Successfully fetched data for indicator: {indicator}")
                    elif "Error Message" in data:
                        error_msg = data["Error Message"]
                        results[indicator] = f"API error: {error_msg}"
                        logger.error(f"Alpha Vantage API error for {indicator}: {error_msg}")
                    else:
                        results[indicator] = "No data or unexpected response format"
                        logger.warning(f"No data or unexpected response for {indicator}: {data}")
            except aiohttp.ClientError as e:
                results[indicator] = f"Network or HTTP request failed: {str(e)}"
                logger.error(f"aiohttp.ClientError for {indicator}: {e}", exc_info=True)
            except Exception as e:
                results[indicator] = f"An unexpected error occurred: {str(e)}"
                logger.critical(f"Unexpected error fetching {indicator}: {e}", exc_info=True)
            await asyncio.sleep(1) # Avoid rate limiting
    return results

@tool(description='A tool to get historical market performance for a given sector.')
async def get_historical_market_performance_sector(sector: str, start_date: str, end_date: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Fetches historical market performance for a given sector from Financial Modeling Prep API.

    Args:
        sector (str): The name of the sector (e.g., "Technology").
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: A list of historical performance data
                                                    or an error dictionary.

    Raises:
        ValueError: If the FPREP API key is not set or dates are invalid.
    """
    logger.info(f"Fetching historical market performance for sector: {sector} from {start_date} to {end_date}")
    try:
        validated_start_date = validate_date(start_date)
        validated_end_date = validate_date(end_date)
    except ValueError as e:
        return {"error": str(e)}

    sector_model = model.with_structured_output(Sector)
    if sector not in VALID_SECTORS:
        logger.warning(f"Attempting to correct invalid sector name: {sector}")
        try:
            corrected_sector_obj = sector_model.invoke(f"Correct the sector: {sector}")
            sector = corrected_sector_obj.sector
            if sector not in VALID_SECTORS:
                logger.error(f"Corrected sector '{sector}' is still not valid.")
                return {"error": f"Invalid sector name: {sector}. Please provide a valid sector."}
            logger.info(f"Sector corrected to: {sector}")
        except Exception as e:
            logger.error(f"Error correcting sector name: {e}", exc_info=True)
            return {"error": f"Could not validate or correct sector name: {str(e)}"}

    api_key = os.getenv('FPREP')
    if not api_key:
        logger.error("FPREP API key not found in environment variables.")
        raise ValueError("FPREP API key is not set in environment variables.")

    url = 'https://financialmodelingprep.com/api/v3/historical-sector-performance'
    params = {'apikey': api_key, 'sector': sector, 'from': validated_start_date, 'to': validated_end_date}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                if not data:
                    logger.warning(f"No historical market performance data found for sector {sector} between {start_date} and {end_date}.")
                    return {"message": f"No data found for sector {sector} in the specified date range."}
                logger.info(f"Successfully fetched historical market performance for sector: {sector}")
                return data
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching historical market performance for {sector}: {e}", exc_info=True)
        return {"error": f"Network or HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.critical(f"An unexpected error occurred fetching historical market performance for {sector}: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
