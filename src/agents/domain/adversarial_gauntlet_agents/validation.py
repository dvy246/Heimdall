from langgraph.prebuilt import create_react_agent
from src.prompts import load_prompt
from src.config.settings import model
from src.tools.Rag.rag import query_data
from src.tools.utilities.extra import search_web
from src.tools.Market.news import get_current_markettrends, get_market_status
from src.model_schemas.schemas import ComprehensiveFactCheck, EvalReport, ValidationReport
from src.tools.utilities.evaluate import evaluate_report
from src.tools.utilities.extra import get_google_finance_data
from src.config.logging_config import logger

logger.info('creating fact checker agent')
fact_checker = create_react_agent(
    model=model,
    tools=[query_data, search_web, get_current_markettrends, get_market_status],
    response_format=ComprehensiveFactCheck,
    name='fact_checker',
    prompt=load_prompt('fact_checker')
)

logger.info('creating evaluator agent')
evaluator_agent = create_react_agent(
    model=model,
    tools=[evaluate_report],
    response_format=EvalReport,
    name='evaluator',
    prompt=load_prompt('evaluator')
)

logger.info('creating validator agent')
validator_agent = create_react_agent(
    model=model,
    tools=[search_web,get_google_finance_data,query_data],
    response_format=ValidationReport,
    name='validator',
    prompt=load_prompt('validator')
)
