from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from src.prompts import load_prompt
from src.tools.utilities.extra import search_web2,get_google_finance_data,get_yahoo_news
from src.config.logging_config import logger
from src.tools.Rag.rag import query_data
from src.model_schemas.schemas import GroundingReport
from src.tools.data_providers.yahoo_finance import fetch_company_analysis

logger.info('creating grounding agent')
grounding_agent=create_react_agent(
    model=model,
    tools=[query_data,search_web2,get_google_finance_data,fetch_company_analysis,get_yahoo_news],
    response_format=GroundingReport,
    name='grounding_agent',
    prompt=load_prompt('grounding_agent')
)
