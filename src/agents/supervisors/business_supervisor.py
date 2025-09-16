from src.prompts import load_supervisor_prompt
from src.config.settings import model
from langgraph_supervisor import create_supervisor
from src.model_schemas.schemas import BusinessOperationsOutput
from src.agents.domain.business_analyst_agents.business_operations import (
    industry_trends_analyst,
    business_segments_analyst, 
    swot_analyst
)

business_operations_team = [
    industry_trends_analyst,
    business_segments_analyst, 
    swot_analyst
]

business_operations_supervisor = create_supervisor(
    business_operations_team,
    model=model,
    response_format=BusinessOperationsOutput,
    prompt=load_supervisor_prompt('business')
).compile(name="business_operations_supervisor")