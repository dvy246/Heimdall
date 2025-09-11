from langgraph.prebuilt import create_react_agent
from src.prompts import load_prompt
from src.config.settings import model
from src.tools.Rag.rag import query_data
from src.tools.utilities.extra import search_web
from src.tools.Market.news import get_current_markettrends, get_market_status
from src.model_schemas.schemas import ComprehensiveFactCheck, EvalReport, ValidationReport

fact_checker = create_react_agent(
    model=model,
    tools=[query_data, search_web, get_current_markettrends, get_market_status],
    response_format=ComprehensiveFactCheck,
    name='fact_checker',
    prompt=load_prompt('fact_checker')
)

evaluator_agent = create_react_agent(
    model=model,
    tools=[],
    response_format=EvalReport,
    name='evaluator',
    prompt=load_prompt('evaluator')
)

validator_agent = create_react_agent(
    model=model,
    tools=[search_web],
    response_format=ValidationReport,
    name='validator',
    prompt=load_prompt('validator')
)
