
import os
import asyncio
import aiohttp
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from src.tools.utilities.extra import run_async_safely
from pydantic import BaseModel, Field

class Interest(BaseModel):
    interest_rate: str = Field(description='the interest rate of the bank')

class InterestRateFetcher:
    def __init__(self):
        self.__api_key = os.getenv('X_API_KEY')
        if not self.__api_key:
            raise ValueError('API key not set in environment')
        self.base_url = 'https://api.financialdatasets.ai'

    async def _fetch_bank_interest_rates(self, bank_name: str, start_date: str, end_date: str = None):
        """Internal async method"""
        try:
            headers = {"X-API-KEY": self.__api_key}
            params = {"bank": bank_name}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/macro/interest-rates',
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        response_text = await response.text()
                        return {"error": f'Failed to get interest rates: {response.status} {response_text}'}
        except Exception as e:
            return {"error": f'Exception occurred while fetching interest rates: {e}'}

    async def _get_snapshot(self):
        """Internal async method"""
        try:
            headers = {"X-API-KEY": self.__api_key}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/macro/interest-rates/snapshot',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        response_text = await response.text()
                        return {"error": f'Failed to get snapshot: {response.status} {response_text}'}
        except Exception as e:
            return {"error": f'Exception occurred while fetching snapshot: {e}'}

# Create global instance
interest_fetcher = InterestRateFetcher()

@tool(description="""
Fetches historical interest rates for a bank.

Args:
- bank_name (string): e.g. 'Bank of America', 'RBI'
- start_date (YYYY-MM-DD): e.g. '2024-01-01'
- end_date (optional, YYYY-MM-DD): e.g. '2024-03-01'

Example call:
fetch_bank_interest_rates(bank_name='RBI', start_date='2024-01-01', end_date='2024-02-01')
""")
def fetch_bank_interest_rates(bank_name: str, start_date: str, end_date: str = None) -> dict:
    """
    Fetches historical interest rates for a specific bank from the Financial Datasets API.

    Args:
        bank_name: The name of the bank to fetch interest rates for
        start_date: The start date for the interest rate data in YYYY-MM-DD format  
        end_date: The end date for the interest rate data in YYYY-MM-DD format (optional)

    Returns:
        Dictionary containing the interest rate data from the API
    """
    return run_async_safely(
        interest_fetcher._fetch_bank_interest_rates(bank_name.upper(), start_date, end_date)
    )

@tool(description='gets snapshot of the interest rates of all the banks')
def get_interest_rates_snapshot() -> dict:
    """
    Fetches a snapshot of current interest rates from the Financial Datasets API.

    Returns:
        Dictionary containing the snapshot data from the API
    """
    return run_async_safely(interest_fetcher._get_snapshot())
