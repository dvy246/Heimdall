# ... existing code ...
from langgraph.prebuilt import create_react_agent
from src.model_schemas.schemas import ESGAnalysisOutput
from src.config.settings import model
from src.config.logging_config import logger
from src.prompts import load_prompt
from src.tools.data_providers.yahoo_finance import get_sustainability_data
from src.tools.utilities.extra import search_web2

logger.info('creating esg analyst agent')
sustainability_agent = create_react_agent(
    model=model,
    tools=[get_sustainability_data, search_web2],
    name="esg_analyst",
    response_format=ESGAnalysisOutput,
    prompt=load_prompt('esg_analyst')
)
