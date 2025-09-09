import os
import aiohttp
import json
import finnhub
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal, Union
from langchain_core.tools import tool
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from src.config.logging_config import logger

# --- Company Overview & Filings ---

@tool(description="Gets comprehensive information about a company from Alpha Vantage API.")
async def company_overview(ticker: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Retrieves detailed company information including financial metrics,
    business description, and key statistics from Alpha Vantage API.

    Args:
        ticker (str): The stock ticker symbol of the company.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: A dictionary containing company overview data or an error message.

    Raises:
        ValueError: If the Alpha Vantage API key is not set.
    """
    logger.info(f"Fetching company overview for ticker: {ticker}")
    api_key = os.getenv('Alpha_Vantage_Stock_API')
    if not api_key:
        logger.error("Alpha_Vantage_Stock_API key not found in environment variables.")
        raise ValueError("Alpha_Vantage_Stock_API key is not set in environment variables.")
    
    try:
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
        if "Note" in data or not data:
            error_msg = data.get("Note", f"No data found for {ticker}. The ticker might be invalid or API limit reached.")
            logger.warning(f"Company overview failed for {ticker}: {error_msg}")
            return {"error": error_msg}
            
        logger.info(f"Successfully fetched company overview for {ticker}.")
        return data
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching company overview for {ticker}: {e}", exc_info=True)
        return {'error': f"Network or HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.critical(f"Unexpected error fetching company overview for {ticker}: {e}", exc_info=True)
        return {'error': f"An unexpected error occurred: {str(e)}"}

@tool(description='Gets the latest 10-K filing for a company.')
async def get_latest_10k_filing(ticker: str) -> str:
    """
    Asynchronously fetches the full text of the most recent 10-K filing for a given company ticker.

    Args:
        ticker (str): The stock ticker symbol of the company.

    Returns:
        str: The full text of the 10-K filing or an error message.

    Raises:
        ValueError: If the SEC_API_KEY or EDGAR_USER_AGENT is not set.
    """
    logger.info(f"Fetching latest 10-K filing for {ticker}")
    sec_api_key = os.getenv('SEC_API_KEY')
    edgar_user_agent = os.getenv('EDGAR_USER_AGENT')

    if not sec_api_key:
        logger.error("SEC_API_KEY not found in environment variables.")
        raise ValueError("SEC_API_KEY is not set in environment variables.")
    if not edgar_user_agent:
        logger.error("EDGAR_USER_AGENT not found in environment variables.")
        raise ValueError("EDGAR_USER_AGENT is not set in environment variables. This is required for SEC filings.")

    try:
        from sec_api import QueryApi
        from bs4 import BeautifulSoup

        query_api = QueryApi(api_key=sec_api_key)
        query = {
            "query": {"query_string": {"query": f'ticker:{ticker} AND formType:"10-K"'}},
            "from": 0, "size": 1, "sort": [{"filedAt": {"order": "desc"}}],
        }
        response = query_api.get_filings(query=query)
        
        if not response or not response.get("filings"):
            logger.warning(f"No 10-K filings found for ticker {ticker}.")
            return f"Error: No 10-K filings found for ticker {ticker}."

        filing_url = response["filings"][0].get("linkToHtml")
        if not filing_url:
            logger.warning(f"Could not find a filing URL for {ticker}.")
            return f"Error: Could not find a filing URL for {ticker}."

        async with aiohttp.ClientSession() as session:
            async with session.get(filing_url, headers={'User-Agent': edgar_user_agent}) as resp:
                resp.raise_for_status()
                filing_html = await resp.text()

        soup = BeautifulSoup(filing_html, 'html.parser')
        cleaned_text = soup.get_text(separator='\n', strip=True)
        logger.info(f"Successfully fetched and parsed latest 10-K for {ticker}.")
        return cleaned_text
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching 10-K for {ticker}: {e}", exc_info=True)
        return f"Error: Network or HTTP request failed while fetching SEC data: {str(e)}"
    except Exception as e:
        logger.critical(f"An unexpected error occurred while fetching the SEC data for {ticker}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while fetching the SEC data: {str(e)}"

# --- Financial Statements ---

@tool(description='Gives back the income statement of the company.')
async def get_income_statements(ticker: str, period: Literal['annual', 'quarter']) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Fetches the income statement of the specified company ticker from Financial Modeling Prep API.

    Args:
        ticker (str): The stock ticker symbol of the company.
        period (Literal['annual', 'quarter']): The period for the income statement ('annual' or 'quarter').

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: A list of income statements or an error message.

    Raises:
        ValueError: If the FPREP API key is not set.
    """
    logger.info(f"Fetching {period} income statements for ticker: {ticker}")
    api_key = os.getenv("FPREP")
    if not api_key:
        logger.error("FPREP API key not found in environment variables.")
        raise ValueError("FPREP API key is not set in environment variables.")
    
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period={period}&apikey={api_key}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                if not data:
                    logger.warning(f"No {period} income statements found for {ticker}.")
                    return {"message": f"No {period} income statements found for {ticker}."}
                logger.info(f"Successfully fetched {period} income statements for {ticker}.")
                return data
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching income statements for {ticker}: {e}", exc_info=True)
        return {"error": f"Network or HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.critical(f"An unexpected error occurred fetching income statements for {ticker}: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

@tool(description='Gives back the cash flow statement of the company.')
async def get_cashflow(ticker: str, period: Literal['annual', 'quarter']) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Fetches the cash flow statement of the specified company ticker from Financial Modeling Prep API.

    Args:
        ticker (str): The stock ticker symbol of the company.
        period (Literal['annual', 'quarter']): The period for the cash flow statement ('annual' or 'quarter').

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: A list of cash flow statements or an error message.

    Raises:
        ValueError: If the FPREP API key is not set.
    """
    logger.info(f"Fetching {period} cash flow statements for ticker: {ticker}")
    api_key = os.getenv("FPREP")
    if not api_key:
        logger.error("FPREP API key not found in environment variables.")
        raise ValueError("FPREP API key is not set in environment variables.")
    url = f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period={period}&apikey={api_key}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                if not data:
                    logger.warning(f"No {period} cash flow statements found for {ticker}.")
                    return {"message": f"No {period} cash flow statements found for {ticker}."}
                logger.info(f"Successfully fetched {period} cash flow statements for {ticker}.")
                return data
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching cash flow statements for {ticker}: {e}", exc_info=True)
        return {"error": f"Network or HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.critical(f"An unexpected error occurred fetching cash flow statements for {ticker}: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

@tool(description='Gives back the balance sheet of the company.')
async def get_balance_sheet(ticker: str, period: Literal['annual', 'quarter'] = 'annual') -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Fetches the balance sheet of the specified company ticker from Alpha Vantage API.

    Args:
        ticker (str): The stock ticker symbol of the company.
        period (Literal['annual', 'quarter']): The period for the balance sheet ('annual' or 'quarter').

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: A list of balance sheets or an error message.

    Raises:
        ValueError: If the Alpha Vantage API key is not set.
    """
    logger.info(f"Fetching {period} balance sheet for ticker: {ticker}")
    api_key = os.getenv('Alpha_Vantage_Stock_API')
    if not api_key:
        logger.error("Alpha_Vantage_Stock_API key not found in environment variables.")
        raise ValueError("Alpha_Vantage_Stock_API key is not set in environment variables.")
    url = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}&period={period}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                reports = data.get('annualReports', []) if period == 'annual' else data.get('quarterlyReports', [])
                if not reports:
                    logger.warning(f"No {period} balance sheet data found for {ticker}.")
                    return {"message": f"No {period} balance sheet data found for {ticker}."}
                logger.info(f"Successfully fetched {period} balance sheet for {ticker}.")
                return reports
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching balance sheet for {ticker}: {e}", exc_info=True)
        return {"error": f"Network or HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.critical(f"An unexpected error occurred fetching balance sheet for {ticker}: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

@tool(description='Gives back the key metrics (earnings) of the company.')
async def get_earnings(ticker: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Fetches the key financial metrics (earnings) of the specified company ticker from Alpha Vantage API.

    Args:
        ticker (str): The stock ticker symbol of the company.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: A list of annual earnings data or an error message.

    Raises:
        ValueError: If the Alpha Vantage API key is not set.
    """
    logger.info(f"Fetching earnings for ticker: {ticker}")
    api_key = os.getenv('Alpha_Vantage_Stock_API')
    if not api_key:
        logger.error("Alpha_Vantage_Stock_API key not found in environment variables.")
        raise ValueError("Alpha_Vantage_Stock_API key is not set in environment variables.")
    url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={api_key}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                annual_earnings = data.get('annualEarnings', [])
                if not annual_earnings:
                    logger.warning(f"No annual earnings data found for {ticker}.")
                    return {"message": f"No annual earnings data found for {ticker}."}
                logger.info(f"Successfully fetched earnings for {ticker}.")
                return annual_earnings
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching earnings for {ticker}: {e}", exc_info=True)
        return {"error": f"Network or HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.critical(f"An unexpected error occurred fetching earnings for {ticker}: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}

# --- Valuation & DCF ---

@tool(description='Gets discounted cash flow and levered discounted cash flow for a company.')
async def get_dcf(ticker: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Fetches Discounted Cash Flow (DCF) data for a given ticker from Financial Modeling Prep API.

    Args:
        ticker (str): The stock ticker symbol of the company.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: A dictionary containing DCF data or an error message.

    Raises:
        ValueError: If the FPREP API key is not set.
    """
    logger.info(f"Fetching DCF data for ticker: {ticker}")
    api_key = os.getenv('FPREP')
    if not api_key:
        logger.error("FPREP API key not found in environment variables.")
        raise ValueError("FPREP API key is not set in environment variables.")

    dcf_url = f'https://financialmodelingprep.com/api/v3/discounted-cash-flow/{ticker}?apikey={api_key}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(dcf_url) as response:
                response.raise_for_status()
                dcf_data = await response.json()
                if not dcf_data:
                    logger.warning(f"No DCF data found for {ticker}.")
                    return {'message': f'No DCF data found for {ticker}.'}
                logger.info(f"Successfully fetched DCF data for {ticker}.")
                return {'dcf': dcf_data[0] if dcf_data else {}}
    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError fetching DCF data for {ticker}: {e}", exc_info=True)
        return {'error': f'Network or HTTP request failed: {str(e)}'}
    except Exception as e:
        logger.critical(f'An unexpected error occurred fetching DCF data for {ticker}: {e}', exc_info=True)
        return {'error': f'An unexpected error occurred: {str(e)}'}

@tool(description='Calculate free cash flow (FCF).')
def free_cash_flow(ebit: float, tax_rate: float, depr_amort: float, capex: float, nwc_change: float) -> float:
    """
    Calculates Free Cash Flow (FCF).

    Args:
        ebit (float): Earnings Before Interest and Taxes.
        tax_rate (float): Company's tax rate.
        depr_amort (float): Depreciation and Amortization.
        capex (float): Capital Expenditures.
        nwc_change (float): Change in Net Working Capital.

    Returns:
        float: The calculated Free Cash Flow.
    """
    logger.info(f"Calculating FCF with Ebit: {ebit}, Tax Rate: {tax_rate}, Depr/Amort: {depr_amort}, Capex: {capex}, NWC Change: {nwc_change}")
    if not all(isinstance(arg, (int, float)) for arg in [ebit, tax_rate, depr_amort, capex, nwc_change]):
        logger.error("Invalid input types for FCF calculation. All arguments must be numeric.")
        raise TypeError("All inputs for FCF calculation must be numeric.")
    
    fcf = ebit * (1 - tax_rate) + depr_amort - capex - nwc_change
    logger.info(f"Calculated FCF: {fcf}")
    return fcf

@tool(description='Calculates the WACC for DCF valuation.')
def calculate_wacc(rfr: float, beta: float, mrp: float, cod: float, tax_rate: float, mve: float, mvd: float) -> float:
    """
    Calculates Weighted Average Cost of Capital (WACC) given all components.

    Args:
        rfr (float): Risk-Free Rate.
        beta (float): Equity Beta.
        mrp (float): Market Risk Premium.
        cod (float): Cost of Debt.
        tax_rate (float): Company's Tax Rate.
        mve (float): Market Value of Equity.
        mvd (float): Market Value of Debt.

    Returns:
        float: The calculated WACC.
    """
    logger.info(f"Calculating WACC with RFR: {rfr}, Beta: {beta}, MRP: {mrp}, CoD: {cod}, Tax Rate: {tax_rate}, MVE: {mve}, MVD: {mvd}")
    if not all(isinstance(arg, (int, float)) for arg in [rfr, beta, mrp, cod, tax_rate, mve, mvd]):
        logger.error("Invalid input types for WACC calculation. All arguments must be numeric.")
        raise TypeError("All inputs for WACC calculation must be numeric.")

    if mve + mvd == 0:
        logger.error("Total value of equity and debt cannot be zero for WACC calculation.")
        raise ValueError("Total market value (MVE + MVD) cannot be zero.")

    total_value = mve + mvd
    weight_equity = mve / total_value
    weight_debt = mvd / total_value
    cost_of_equity = rfr + (beta * mrp)
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cod * (1 - tax_rate))
    logger.info(f"Calculated WACC: {wacc}")
    return wacc

@tool(description='Use to calculate DCF of the company.')
def dcf_analyst(fcf: List[float], tgr: float, wacc: float, net_debt: float, shares_out: float) -> Dict[str, float]:
    """
    Performs a complete Discounted Cash Flow (DCF) calculation to determine intrinsic value per share.

    Args:
        fcf (List[float]): List of forecasted Free Cash Flows.
        tgr (float): Terminal Growth Rate.
        wacc (float): Weighted Average Cost of Capital.
        net_debt (float): Company's Net Debt.
        shares_out (float): Number of Shares Outstanding.

    Returns:
        Dict[str, float]: A dictionary containing the intrinsic value per share.

    Raises:
        ValueError: If WACC is less than or equal to TGR, or if shares outstanding is zero.
        TypeError: If input types are not numeric.
    """
    logger.info(f"Performing DCF analysis with FCF: {fcf}, TGR: {tgr}, WACC: {wacc}, Net Debt: {net_debt}, Shares Out: {shares_out}")
    if not all(isinstance(arg, (int, float)) for arg in fcf + [tgr, wacc, net_debt, shares_out]):
        logger.error("Invalid input types for DCF calculation. All arguments must be numeric.")
        raise TypeError("All inputs for DCF calculation must be numeric.")

    if wacc <= tgr:
        logger.error(f"WACC ({wacc}) must be greater than Terminal Growth Rate ({tgr}) for a valid DCF calculation.")
        raise ValueError("WACC must be greater than Terminal Growth Rate.")
    if shares_out <= 0:
        logger.error("Shares outstanding must be greater than zero for intrinsic value calculation.")
        raise ValueError("Shares outstanding must be greater than zero.")

    pv_fcf = [cf / ((1 + wacc) ** (i + 1)) for i, cf in enumerate(fcf)]
    terminal_value = (fcf[-1] * (1 + tgr)) / (wacc - tgr)
    pv_terminal_value = terminal_value / ((1 + wacc) ** len(fcf))
    enterprise_value = sum(pv_fcf) + pv_terminal_value
    equity_value = enterprise_value - net_debt
    intrinsic_value = equity_value / shares_out
    logger.info(f"Calculated intrinsic value per share: {intrinsic_value}")
    return {'intrinsic_value': intrinsic_value}

# --- Other Financial Tools ---

@tool(description='To get sustainability data.')
def get_sustainability_data(ticker: str) -> str:
    """
    Retrieves ESG sustainability metrics for a company using yfinance.

    Args:
        ticker (str): The stock ticker symbol of the company.

    Returns:
        str: JSON string of sustainability data or an error message.
    """
    logger.info(f"Fetching sustainability data for ticker: {ticker}")
    try:
        ticker_obj = yf.Ticker(ticker)
        sustainability_data = ticker_obj.sustainability
        if sustainability_data is not None and not sustainability_data.empty:
            logger.info(f"Successfully fetched sustainability data for {ticker}.")
            return sustainability_data.to_json()
        else:
            logger.warning(f"No sustainability data available for {ticker}.")
            return "No data available"
    except Exception as e:
        logger.error(f"Error fetching sustainability data for {ticker}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while fetching sustainability data: {str(e)}"

@tool(description='To get major holders data.')
def get_major_holders(ticker: str) -> str:
    """
    Fetches information about the largest shareholders of a company using yfinance.

    Args:
        ticker (str): The stock ticker symbol of the company.

    Returns:
        str: JSON string of major holders data or an error message.
    """
    logger.info(f"Fetching major holders data for ticker: {ticker}")
    try:
        ticker_obj = yf.Ticker(ticker)
        major_holders = ticker_obj.major_holders
        if major_holders is not None and not major_holders.empty:
            logger.info(f"Successfully fetched major holders data for {ticker}.")
            return major_holders.to_json()
        else:
            logger.warning(f"No major holders data available for {ticker}.")
            return "No data available"
    except Exception as e:
        logger.error(f"Error fetching major holders data for {ticker}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while fetching major holders data: {str(e)}"

@tool(description='To get financial statements data.')
def get_financials(ticker: str) -> str:
    """
    Retrieves comprehensive financial statements (income statement, balance sheet, cash flow) using yfinance.

    Args:
        ticker (str): The stock ticker symbol of the company.

    Returns:
        str: JSON string of financial statements data or an error message.
    """
    logger.info(f"Fetching financial statements data for ticker: {ticker}")
    try:
        ticker_obj = yf.Ticker(ticker)
        financials = ticker_obj.financials
        if not financials.empty:
            logger.info(f"Successfully fetched financial statements data for {ticker}.")
            return financials.to_json()
        else:
            logger.warning(f"No financial statements data found for {ticker}.")
            return "No data found"
    except Exception as e:
        logger.error(f"Error fetching financial statements data for {ticker}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while fetching financial statements data: {str(e)}"
