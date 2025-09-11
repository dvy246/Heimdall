from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from src.prompts import load_prompt
from src.tools.utilities.extra import search_web2, get_current_date
from src.tools.Market.news import get_current_markettrends

strategist_agent = create_react_agent(
    model=model,
    tools=[get_current_date, get_current_markettrends, search_web2],
    name='strategist',
    prompt=load_prompt('strategist')
)