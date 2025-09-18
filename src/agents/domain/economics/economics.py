from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from src.tools.data_providers.alpha_vantage import get_economic_indicators, get_global_market_status
from src.tools.Market.news import get_current_markettrends
from src.tools.utilities.extra import search_web2
from src.prompts import load_prompt
from src.config.logging_config import logger

logger.info('creating economics team agents')

economics_team = [
    create_react_agent(
        model=model,
        tools=[get_economic_indicators, get_current_markettrends, search_web2],
        name='macro_agent',
        prompt=load_prompt('macro_agents')
    ),
    create_react_agent(
        model=model,
        tools=[get_economic_indicators, get_current_markettrends, search_web2, get_global_market_status],
        name='global_economic_agent',
        prompt=load_prompt('global_economic_agents')
    )
]

