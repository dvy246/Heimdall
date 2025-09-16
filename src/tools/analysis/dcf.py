import os
import aiohttp
import asyncio
import numpy as np
from typing import Dict, List
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from langchain.tools import tool
from src.tools.utilities.ticker_conversion import validate_ticker_symbol
from src.config.logging_config import logger

@tool('gets discounted cash flow and levered discounted cash flow for a company')
async def get_dcf(ticker: str):
    """
    Asynchronously fetches both the DCF (Discounted Cash Flow) and Levered DCF for a given ticker from Financial Modeling Prep.

    Args:
        ticker (str): The ticker symbol to fetch the DCFs for (e.g., 'AAPL').

    Returns:
        dict: The DCF and Levered DCF data for the ticker, or an error message if the request fails.
    """
    logger.info(f"Fetching DCF and Levered DCF for ticker: {ticker}")
    if not isinstance(ticker, str) or not ticker.isalnum() or len(ticker) > 10:
        logger.error("Invalid ticker symbol")
        return {'error': 'Invalid ticker symbol. Must be alphanumeric and up to 10 characters.'}
    
    ticker = validate_ticker_symbol(ticker)
    if not ticker:
        logger.error("Ticker symbol validation failed")
        return {'error': 'Invalid ticker symbol.'}
    
    api_key = os.getenv('FPREP')
    if not api_key:
        logger.error("FPREP environment variable not set")
        return {'error': 'FPREP environment variable not set'}

    dcf_url = 'https://financialmodelingprep.com/stable/discounted-cash-flow'
    levered_dcf_url = 'https://financialmodelingprep.com/stable/levered-discounted-cash-flow'
    params = {'apikey': api_key, 'symbol': ticker}

    try:
        async with aiohttp.ClientSession() as session:
            logger.info("Making API requests for DCF and Levered DCF")
            dcf_task = session.get(dcf_url, params=params)
            levered_dcf_task = session.get(levered_dcf_url, params=params)
            dcf_response, levered_dcf_response = await asyncio.gather(dcf_task, levered_dcf_task)
            
            async with dcf_response:
                dcf_data = await dcf_response.json()
            async with levered_dcf_response:
                levered_dcf_data = await levered_dcf_response.json()

            result = {}

            if dcf_response.status == 200:
                if not dcf_data:
                    logger.warning(f"No DCF data found for ticker: {ticker}")
                    result['dcf'] = {'error': f'No DCF data found for ticker: {ticker}'}
                elif isinstance(dcf_data, dict) and 'error' in dcf_data:
                    logger.error(f"Error in DCF response: {dcf_data.get('error')}")
                    result['dcf'] = {'error': dcf_data.get('error')}
                elif isinstance(dcf_data, list):
                    dcf_entry = dcf_data[0] if dcf_data else {}
                    dcf_value = dcf_entry.get('dcf')
                    stock_value = dcf_entry.get('Stock Price')
                    try:
                        logger.info(f"DCF value: {float(dcf_value):.1f}, Stock price: {stock_value}")
                    except (TypeError, ValueError):
                        logger.error("Unexpected DCF response format")
                    result['dcf'] = dcf_entry
                else:
                    logger.error("Unexpected DCF response format")
                    result['dcf'] = {'error': f'Unexpected DCF response format: {dcf_data}'}
            else:
                result['dcf'] = {'error': f'Failed to fetch DCF data: HTTP {dcf_response.status}'}

            if levered_dcf_response.status == 200:
                if not levered_dcf_data:
                    logger.warning(f"No Levered DCF data found for ticker: {ticker}")
                    result['levered_dcf'] = {'error': f'No Levered DCF data found for ticker: {ticker}'}
                elif isinstance(levered_dcf_data, dict) and 'error' in levered_dcf_data:
                    logger.error(f"Error in Levered DCF response: {levered_dcf_data.get('error')}")
                    result['levered_dcf'] = {'error': levered_dcf_data.get('error')}
                elif isinstance(levered_dcf_data, list):
                    levered_dcf_entry = levered_dcf_data[0] if levered_dcf_data else {}
                    levered_dcf_value = levered_dcf_entry.get('leveredDCF')
                    if levered_dcf_value is None:
                        levered_dcf_value = levered_dcf_entry.get('dcf')
                    stock_value = levered_dcf_entry.get('Stock Price')
                    try:
                        logger.info(f"Levered DCF value: {float(levered_dcf_value):.1f}, Stock price: {stock_value}")
                    except (TypeError, ValueError):
                        logger.error("Unexpected Levered DCF response format")
                    result['levered_dcf'] = levered_dcf_entry
                else:
                    logger.error("Unexpected Levered DCF response format")
                    result['levered_dcf'] = {'error': f'Unexpected Levered DCF response format: {levered_dcf_data}'}
            else:
                logger.error(f"Failed to fetch Levered DCF data: HTTP {levered_dcf_response.status}")
                result['levered_dcf'] = {'error': f'Failed to fetch Levered DCF data: HTTP {levered_dcf_response.status}'}

            return result

    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
        return {'error': f'HTTP request failed: {e}'}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {'error': f'An unexpected error occurred: {e}'}

@tool(description='get net working capital')
def nwc(current_operating_asset:list[float], current_operating_libalities:list[float])-> float:
    """
    Calculate Net Working Capital (NWC).

    Net Working Capital is defined as the difference between current operating assets and current operating liabilities.

    Args:
        current_operating_assets (float): The total current operating assets.
        current_operating_libalities (float): The total current operating liabilities.

    Returns:
        float: The calculated net working capital.
        dict: An error dictionary if an exception occurs.
    """
    logger.info(f"Calculating NWC with assets: {current_operating_asset}, liabilities: {current_operating_libalities}")
    ca = current_operating_asset
    cl = current_operating_libalities
    try:
        working_capital = sum(ca) - sum(cl)
        logger.info(f"Calculated NWC: {working_capital}")
        return float(working_capital)
    except Exception as e:
        logger.error(f"An unexpected error occurred while calculating NWC: {e}")
        return {'error': f'An unexpected error occurred: {e}'}

@tool(description='Calculate free cash flow (FCF) given EBIT, tax rate, depreciation & amortization, capital expenditures, and change in working capital.')
def free_cash_flow(
    ebit: float,
    tax_rate: float,
    depreciation_and_amortization: float,
    capital_expenditures: float,
    change_in_working_capital: float
) -> float:
    """
    Calculate Free Cash Flow (FCF).

    Free Cash Flow (FCF) is defined as:
        FCF = EBIT * (1 - tax_rate) + Depreciation & Amortization - Capital Expenditures - Change in Working Capital

    Args:
        ebit (float): Earnings Before Interest and Taxes.
        tax_rate (float): The tax rate as a decimal (e.g., 0.21 for 21%).
        depreciation_and_amortization (float): Total depreciation and amortization.
        capital_expenditures (float): Total capital expenditures.
        change_in_working_capital (float): Change in net working capital (increase is a cash outflow).

    Returns:
        float: The calculated free cash flow.
        dict: An error dictionary if an exception occurs.
    """
    logger.info(f"Calculating FCF with EBIT: {ebit}, tax_rate: {tax_rate}, D&A: {depreciation_and_amortization}, CapEx: {capital_expenditures}, ΔWC: {change_in_working_capital}")
    try:
        fcf = ebit * (1 - tax_rate) + depreciation_and_amortization - capital_expenditures - change_in_working_capital
        logger.info(f"Calculated FCF: {fcf}")
        return float(fcf)
    except Exception as e:
        logger.error(f"An error occurred while calculating free cash flow: {e}")
        return {'error': f'An error occurred while calculating free cash flow: {e}'}

@tool(description='Calculates the WACC for DCF valuation of the company')
def calculate_wacc(
    risk_free_rate: float,
    beta: float, 
    market_risk_premium: float,
    cost_of_debt: float,
    tax_rate: float,
    market_value_equity: float,
    market_value_debt: float
) -> float:
    """
    Calculate WACC given all components.
    WACC = (E/V) * Re + (D/V) * Rd * (1-T)
    Returns the WACC as a float (decimal, e.g., 0.085 for 8.5%).
    """
    logger.info(f"Calculating WACC with risk_free_rate: {risk_free_rate}, beta: {beta}, market_risk_premium: {market_risk_premium}")
    logger.info(f"Cost of debt: {cost_of_debt}, tax_rate: {tax_rate}, equity value: {market_value_equity}, debt value: {market_value_debt}")
    try:
        total_value = market_value_equity + market_value_debt
        if total_value == 0:
            logger.error("Total market value (equity + debt) is zero")
            raise ValueError('Total market value (equity + debt) is zero.')
        weight_equity = market_value_equity / total_value
        weight_debt = market_value_debt / total_value
        cost_of_equity = risk_free_rate + (beta * market_risk_premium)
        after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)
        wacc = (weight_equity * cost_of_equity) + (weight_debt * after_tax_cost_of_debt)
        logger.info(f"Calculated WACC: {wacc:.4f} ({wacc*100:.2f}%)")
        return float(wacc)
    except Exception as e:
        logger.error(f"Error calculating WACC: {e}")
        return float('nan')
        
@tool(description='net debt')
def net_debt(total_debt:float,cash:float):
    logger.info(f"Calculating net debt with total debt: {total_debt}, cash: {cash}")
    try:
        net_debt_value = total_debt - cash
        logger.info(f"Calculated net debt: {net_debt_value}")
        return float(net_debt_value)
    except Exception as e:
        logger.error(f"An error occurred while calculating net debt: {e}")
        return {'error': f'An error occurred while calculating net debt: {e}'}

@tool(description='use to calculate dcf of the company')
def dcf_analyst(
    projected_fcf: List[float],
    terminal_growth_rate: float,
    wacc: float,
    net_debt: float,
    shares_outstanding: float
) -> Dict:
    """
    Complete DCF calculation: projects FCF, calculates terminal value, 
    discounts to present value, and derives per-share value.
    """
    logger.info(f"Starting DCF analysis with projected FCF: {projected_fcf}")
    logger.info(f"Terminal growth rate: {terminal_growth_rate}%, WACC: {wacc}%, Net debt: {net_debt}, Shares: {shares_outstanding}")
    
    if not projected_fcf or wacc<=terminal_growth_rate:
        logger.error("Invalid inputs for DCF calculation")
        return {'error': "Invalid inputs for DCF calculation."}
    try:
        wacc_decimal = wacc / 100.0
        terminal_growth_rate_decimal = terminal_growth_rate / 100.0
        pv_fcf=[]

        for year,fcf in enumerate(projected_fcf,1):
            pv = fcf / ((1 + wacc_decimal) ** year)
            pv_fcf.append(pv)
            logger.debug(f"Year {year} FCF: {fcf}, PV: {pv}")
         
        final_fcf=projected_fcf[-1]
        terminal_value = (final_fcf * (1 + terminal_growth_rate_decimal)) / (wacc_decimal - terminal_growth_rate_decimal)
        logger.info(f"Terminal value: {terminal_value}")

        pv_terminal_value = terminal_value / ((1 + wacc_decimal) ** len(projected_fcf))
        enterprise_value = sum(pv_fcf) + pv_terminal_value
        logger.info(f"Enterprise value: {enterprise_value}")

        equity_value = enterprise_value - net_debt
        logger.info(f"Equity value: {equity_value}")
        
        intrinsic_value_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0
        logger.info(f"Intrinsic value per share: {intrinsic_value_per_share}")
        
        return {
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'intrinsic_value_per_share': intrinsic_value_per_share,
            'pv_projected_fcf': pv_fcf,
            'terminal_value': terminal_value,
            'pv_terminal_value': pv_terminal_value,
            'wacc_used': wacc,
            'terminal_growth_rate_used': terminal_growth_rate
        }
    except Exception as e:
        logger.error(f"An error occurred in DCF calculation: {e}")
        return {'error': f"An error occurred in DCF calculation: {e}"}

@tool(description='forecast future cash flows')
def forecast_unleveredc_cash_flows(historical_fcf: List[float], projection_period: int = 5) -> Dict:
    """
    Forecast future cash flows based on historical FCF data using a linear regression model.

    Args:
        historical_fcf (List[float]): List of historical FCF values.
        projection_period (int): The number of periods to forecast into the future. Defaults to 5.

    Returns:
        Dict: A dictionary containing the forecasted FCF values and assumptions used in the forecast.
    """
    logger.info(f"Forecasting cash flows for {projection_period} periods into the future")
    logger.info(f"Historical FCF data: {historical_fcf}")
    
    if not historical_fcf or len(historical_fcf) < 2:
        logger.error("Invalid inputs for FCF forecast - insufficient historical data")
        return {'error': "Invalid inputs for FCF forecast."}

    try:
        periods = np.array(range(1, len(historical_fcf) + 1)).reshape(-1, 1)
        historical_fcf = np.array(historical_fcf)

        model = LinearRegression()
        model.fit(periods, historical_fcf)

        slope = model.coef_[0]
        intercept = model.intercept_

        future_periods = np.array(range(len(historical_fcf) + 1, len(historical_fcf) + projection_period + 1)).reshape(-1, 1)

        projected_fcf = model.predict(future_periods)

        projected_fcf_list = [round(val, 2) for val in projected_fcf.tolist()]

        score = r2_score(historical_fcf, projected_fcf)

        return {
            "projected_fcf": projected_fcf_list,
            "assumptions": {
                "method": "Scikit-Learn Linear Regression",
                "slope": round(slope, 2),
                'r2_score': float(score),
                "intercept": round(intercept, 2),
                "projection_period": projection_period
            }
        }
    except Exception as e:
        logger.error(f"An error occurred in FCF forecast: {e}")
        return {'error': f"An error occurred in FCF forecast: {e}"}