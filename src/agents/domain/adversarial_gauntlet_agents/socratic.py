from langgraph.prebuilt import create_react_agent
from src.tools.utilities.extra import search_web2,get_google_finance_data
from src.config.settings import model
from src.model_schemas.schemas import SocraticQuestions
from src.prompts import load_prompt
from src.tools.Rag.rag import query_data
from src.config.logging_config import logger


logger.info('creating socratic agent')
socratic_agent=create_react_agent(
    model=model,
    tools=[search_web2,get_google_finance_data,query_data],
    prompt=load_prompt('socratic_agent'),
    response_format=SocraticQuestions,
    name='socratic_agent'
)