from src.str_model.strmdls import sector_model


@tool('gets overview of the company')
async def get_company_overview(ticker: str) -> Dict[str, Any]:
    """
    Fetches an overview for a specific ticker from Finnhub.io.

    Args:
        ticker (str): The ticker symbol to fetch the overview for (e.g., 'AAPL').

    Returns:
        dict: The overview data for the ticker, or an error message if the request fails.
    """
    # Input validation
    if not isinstance(ticker, str) or not ticker.isalnum() or len(ticker) > 10:
        return {"error": "Invalid ticker symbol. Must be alphanumeric and up to 10 characters."}

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return {"error": "Missing FINNHUB_API_KEY environment variable."}

    try:
        finnhub_client = finnhub.Client(api_key=api_key)
        finnhub_client.aggregate_indicator(symbol='MSFT')
    except Exception as e:
        return {"error": f"Failed to initialize Finnhub client: {e}"}

    try:
        company_overview = finnhub_client.company_profile2(symbol=ticker)
        if not company_overview or not isinstance(company_overview, dict) or not company_overview.get("name"):
            return {"error": f"No company overview found for ticker '{ticker}'."}
        return company_overview
    except AttributeError as e:
        return {"error": f"Finnhub client error: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

@tool(description="to get_corporate_actions of the ticker") 
async def get_corporate_actions(symbol: str):
    """
    Fetches corporate actions (specifically dividend events) for a given stock symbol from Alpha Vantage.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: A dictionary containing the symbol and the dividend data if successful,
              or an error message if the request fails or the API key is missing.

    Notes:
        - This function currently retrieves only dividend events using the 'DIVIDENDS' function from Alpha Vantage.
        - Ensure that the 'Alpha_Vantage_Stock_API' environment variable is set with your API key.
        - If the API key is not set, the function will use the 'demo' key, which has limited capabilities.
    """
    api_key = os.getenv('Alpha_Vantage_Stock_API', 'demo')
    if not api_key:
        return {"error": "Alpha Vantage API key is missing. Please set the Alpha_Vantage_Stock_API environment variable."}
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'DIVIDENDS',
        'symbol': symbol,
        'apikey': api_key
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"symbol": symbol, "data": data}
                else:
                    return {"error": f"HTTP status {response.status}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

@tool(description="to get_stock_splits of the ticker")
async def get_stock_splits(symbol: str):
    """
    Fetches stock split events for a given stock symbol from Alpha Vantage.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'IBM').

    Returns:
        dict: A dictionary containing the symbol and the split data if successful,
              or an error message if the request fails or the API key is missing.

    Notes:
        - This function retrieves stock split events using the 'SPLITS' function from Alpha Vantage.
        - Ensure that the 'Alpha_Vantage_Stock_API' environment variable is set with your API key.
        - If the API key is not set, the function will use the 'demo' key, which has limited capabilities.
    """
    api_key = os.getenv('Alpha_Vantage_Stock_API', 'demo')
    if not api_key:
        return {"error": "Alpha Vantage API key is missing. Please set the Alpha_Vantage_Stock_API environment variable."}
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'SPLITS',
        'symbol': symbol,
        'apikey': api_key
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"symbol": symbol, "data": data}
                else:
                    return {"error": f"HTTP status {response.status}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

from regex.regex import I


@tool("get_ticker_overview", return_direct=True)
async def get_ticker_overview(ticker: str, date: str = None) -> dict:
    """
    Fetches an overview for a specific ticker from Polygon.io.

    Args:
        ticker (str): The ticker symbol to fetch the overview for (e.g., 'AAPL').
        date (str, optional): The date for which to fetch the overview in 'YYYY-MM-DD' format. If not provided, the latest available data is returned.

    Returns:
        dict: The overview data for the ticker, or an error message if the request fails.
    """
    import os
    import aiohttp

    api = os.getenv('polygon_api')
    if not api:
        return {"error": "Missing POLYGON_API_KEY environment variable"}

    url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
    params = {"apiKey": api}
    if date:
        try:
            params["date"] = validate_date(date)
        except Exception as e:
            return {"error": f"Invalid date format: {str(e)}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP status {response.status}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}
        
@tool('gets overview of the company')
async def get_company_overview(ticker: str) -> Dict[str, Any]:
    """
    Fetches an overview for a specific ticker from Finnhub.io.

    Args:
        ticker (str): The ticker symbol to fetch the overview for (e.g., 'AAPL').

    Returns:
        dict: The overview data for the ticker, or an error message if the request fails.
    """
    # Input validation
    if not isinstance(ticker, str) or not ticker.isalnum() or len(ticker) > 10:
        return {"error": "Invalid ticker symbol. Must be alphanumeric and up to 10 characters."}

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return {"error": "Missing FINNHUB_API_KEY environment variable."}

    try:
        finnhub_client = finnhub.Client(api_key=api_key)
        finnhub_client.aggregate_indicator(symbol='MSFT')
    except Exception as e:
        return {"error": f"Failed to initialize Finnhub client: {e}"}

    try:
        company_overview = finnhub_client.company_profile2(symbol=ticker)
        if not company_overview or not isinstance(company_overview, dict) or not company_overview.get("name"):
            return {"error": f"No company overview found for ticker '{ticker}'."}
        return company_overview
    except AttributeError as e:
        return {"error": f"Finnhub client error: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

available_tickers = [
    'AAPL', 'TSLA', 'AMZN', 'MSFT', 'NVDA', 'GOOGL', 'META', 'NFLX', 'JPM', 'V', 'BAC', 'AMD', 'PYPL', 'DIS', 'T',
    'PFE', 'COST', 'INTC', 'KO', 'TGT', 'NKE', 'SPY', 'BA', 'BABA', 'XOM', 'WMT', 'GE', 'CSCO', 'VZ', 'JNJ', 'CVX',
    'PLTR', 'SQ', 'SHOP', 'SBUX', 'SOFI', 'HOOD', 'RBLX', 'SNAP', 'AMD', 'UBER', 'FDX', 'ABBV', 'ETSY', 'MRNA',
    'LMT', 'GM', 'F', 'RIVN', 'LCID', 'CCL', 'DAL', 'UAL', 'AAL', 'TSM', 'SONY', 'ET', 'NOK', 'MRO', 'COIN', 'RIVN',
    'SIRI', 'SOFI', 'RIOT', 'CPRX', 'PYPL', 'TGT', 'VWO', 'SPYG', 'NOK', 'ROKU', 'HOOD', 'VIAC', 'ATVI', 'BIDU',
    'DOCU', 'ZM', 'PINS', 'TLRY', 'WBA', 'VIAC', 'MGM', 'NFLX', 'NIO', 'C', 'GS', 'WFC', 'ADBE', 'PEP', 'UNH',
    'CARR', 'FUBO', 'HCA', 'TWTR', 'BILI', 'SIRI', 'VIAC', 'FUBO', 'RKT'
]

def validate_dcf_ticker(ticker: str):
    if ticker not in available_tickers:
        return {'error': 'ticker does not exist'}
    else:
        return ticker


def get_insights(ticker:str,news_data):
    for article in news_data.get('results', []):
        if isinstance(article, dict):
            insights = article.get('insights', [])
            description = article.get('description', '[]')
            for insight in insights:
                if isinstance(insight, dict) and insight.get('ticker') == ticker:
                    print({'insight': insight, 'description': description})

@tool(description="to get_shares_outstanding of the ticker")
async def get_shares_outstanding(symbol: str) -> dict:
    """
    Fetches shares outstanding for a given stock symbol from Alpha Vantage.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: The shares outstanding data, or an error message if the request fails.
    """
    api_key = os.getenv('Alpha_Vantage_Stock_API', 'demo')
    if not api_key:
        return {"error": "Alpha Vantage API key is missing. Please set the Alpha_Vantage_Stock_API environment variable."}
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'SHARES_OUTSTANDING',
        'symbol': symbol,
        'apikey': api_key
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    print('shares outstanding got ')
                    data = await response.json()
                    return {"symbol": symbol, "data": data}
                else:
                    return {"error": f"HTTP status {response.status}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def validate_sector(sector: str):
    if sector not in VALID_SECTORS:
        new_sector = sector_model.invoke(
            f"The sector must be from {VALID_SECTORS} and the given by user is {sector}"
        )
        print(new_sector.sector)
        return new_sector.sector
    else:
        return sector
        
@tool(description='a tool to get historical market performance for a given sector between two dates')
async def get_historical_market_performance_sector(sector: str, frm: str, to: str):
    """
    Fetch historical market performance for a given sector between two dates.

    Parameters
    ----------
    sector : str
        The sector to fetch data for. Must be one of:
            - Energy
            - Technology
            - Healthcare
            - Financial Services
            - Consumer Cyclical
            - Consumer Defensive
            - Industrials
            - Basic Materials
            - Real Estate
            - Utilities
            - Communication Services
    frm : str
        The start date in 'YYYY-MM-DD' format.
    to : str
        The end date in 'YYYY-MM-DD' format.

    Returns
    -------
    list or dict or str
        Sorted list of sector performance data, or an error message.
    """
    # Validate sector before proceeding
    sector = validate_sector(sector)
    frm, to = validate_date(frm), validate_date(to) # Validate dates before proceeding
    api_key = os.getenv('FPREP')
    if not api_key:
        return {'error': 'API key not found'}
    try:
        async with aiohttp.ClientSession() as session:
            url = ' https://financialmodelingprep.com/stable/historical-sector-performance'
            params = {
                'apikey': api_key,
                'sector': sector,
                'from': frm,
                'to': to
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    new = sorted(data, key=lambda x: x['date'], reverse=True)
                    return new
                else:
                    return f"Error: HTTP status {response.status}"
    except Exception as e:
        return f"Request failed: {str(e)}"  


def validate_sector(sector: str):
    if sector not in VALID_SECTORS:
        new_sector = sector_model.invoke(
            f"The sector must be from {VALID_SECTORS} and the given by user is {sector}"
        )
        print(new_sector.sector)
        return new_sector.sector
    else:
        return sector
        
@tool(description='a tool to get historical market performance for a given sector between two dates')
async def get_historical_market_performance_sector(sector: str, frm: str, to: str):
    """
    Fetch historical market performance for a given sector between two dates.

    Parameters
    ----------
    sector : str
        The sector to fetch data for. Must be one of:
            - Energy
            - Technology
            - Healthcare
            - Financial Services
            - Consumer Cyclical
            - Consumer Defensive
            - Industrials
            - Basic Materials
            - Real Estate
            - Utilities
            - Communication Services
    frm : str
        The start date in 'YYYY-MM-DD' format.
    to : str
        The end date in 'YYYY-MM-DD' format.

    Returns
    -------
    list or dict or str
        Sorted list of sector performance data, or an error message.
    """
    # Validate sector before proceeding
    sector = validate_sector(sector)
    frm, to = validate_date(frm), validate_date(to) # Validate dates before proceeding
    api_key = os.getenv('FPREP')
    if not api_key:
        return {'error': 'API key not found'}
    try:
        async with aiohttp.ClientSession() as session:
            url = ' https://financialmodelingprep.com/stable/historical-sector-performance'
            params = {
                'apikey': api_key,
                'sector': sector,
                'from': frm,
                'to': to
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    new = sorted(data, key=lambda x: x['date'], reverse=True)
                    return new
                else:
                    return f"Error: HTTP status {response.status}"
    except Exception as e:
        return f"Request failed: {str(e)}"  


@tool(description='does advanced analytics details of the company')
async def advaced_analyst(
    ticker: list[str],
    interval: str,
    window_size: int,
    calculations: List[str],
    range_str: str,
    ohlc: Optional[str] = "close"
):
    ''' This endpoint returns a rich set of advanced analytics metrics (e.g., total return, variance, auto-correlation, etc.) for a given time series over sliding time windows. For example, we can calculate a moving variance over 5 years with a window of 100 points to see how the variance changes over time.'''
    api = os.getenv('Alpha_Vantage_Stock_API')
    if not api:
        return {"error": "Alpha Vantage API key not found."}

    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "ANALYTICS_SLIDING_WINDOW",
        'SYMBOLS': ticker,
        "RANGE": '6month',
        "INTERVAL": interval,
        "WINDOW_SIZE": window_size,
        "CALCULATIONS": ",".join(calculations),
        "OHLC": ohlc,
        "apikey": api
    }

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        if "Note" in data or not data:
            return {"error": "Could not fetch data. API limit may be reached or parameters are invalid."}

        return data.get("payload", {"error": "No payload found."})

    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}