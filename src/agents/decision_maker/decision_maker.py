from langgraph.prebuilt import create_react_agent
from src.model_schemas.schemas import DecisionOutput
from src.prompts import load_prompt
from src.config.settings import model
from src.config.logging_config import logger
from src.tools.Market.news import get_global_market_status,get_current_markettrends,get_market_status

logger.info('making decision agent')
decision_maker=create_react_agent(
    model=model,
    tools=[get_global_market_status,get_current_markettrends,get_market_status],
    response_format=DecisionOutput,
    name='decision_maker',
    prompt=load_prompt('decision_maker'),
)