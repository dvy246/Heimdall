from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from src.model_schemas.schemas import IndustryTrendsOutput, BusinessSegmentsOutput, SWOTOutput, BusinessOperationsOutput
from src.tools.data_providers.alpha_vantage import get_income_statements, company_overview, get_analyst_recommendation, get_major_holders, get_economic_indicators, get_corporate_actions
from src.tools.data_providers.financial_modeling_prep import fetch_company_financial_analysis
from src.tools.Market.news import get_current_markettrends
from src.tools.utilities.extra import search_web2
from src.config.settings import model
from src.prompts import load_prompt

industry_trends_analyst = create_react_agent(
    model=model,
    tools=[search_web2, get_current_markettrends, company_overview, get_economic_indicators, fetch_company_financial_analysis],
    name="industry_trends_analyst",
    response_format=IndustryTrendsOutput,
    prompt=load_prompt('industry_trends_analyst')
)

# Business Segments Analyst
business_segments_analyst = create_react_agent(
    model=model,
    tools=[get_income_statements, company_overview, search_web2, get_analyst_recommendation, get_major_holders],
    name="business_segments_analyst", 
    response_format=BusinessSegmentsOutput,
    prompt=load_prompt('business_segments_analyst')
)

# SWOT Analysis Agent
swot_analyst = create_react_agent(
    model=model,
    tools=[company_overview, search_web2, get_current_markettrends, fetch_company_financial_analysis, get_income_statements, get_corporate_actions, get_major_holders],
    name="swot_analyst",
    response_format=SWOTOutput,
    prompt=load_prompt('swot_analyst')
)


