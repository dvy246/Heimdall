from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from src.tools.data_providers.alpha_vantage import get_economic_indicators, get_global_market_status
from src.tools.Market.news import get_current_markettrends
from src.tools.utilities.extra import search_web2
from src.tools.data_providers.financialdatasetsai import fetch_bank_interest_rates, get_interest_rates_snapshot
from src.prompts import load_prompt
from src.config.logging_config import logger
from src.tools.data_providers.financialdatasetsai import get_interest_rates_snapshot,fetch_bank_interest_rates
logger.info('creating economics team agents')

economics_team = [
    create_react_agent(
        model=model,
        tools=[get_economic_indicators, get_current_markettrends, search_web2, fetch_bank_interest_rates, get_interest_rates_snapshot],
        name='macro_agent',
        prompt=load_prompt('macro_agents')
    ),
    create_react_agent(
        model=model,
        tools=[get_economic_indicators, get_current_markettrends, search_web2, get_global_market_status, fetch_bank_interest_rates, get_interest_rates_snapshot],
        name='global_economic_agent',
        prompt=load_prompt('global_economic_agents')
    ),
    create_react_agent(
        model=model,
        tools=[ get_current_markettrends, search_web2,get_global_market_status, fetch_bank_interest_rates, get_interest_rates_snapshot],
        name='interest_rates_agent',
        prompt=load_prompt('interest_rates_agents'))
]

