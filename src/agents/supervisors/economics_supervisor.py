from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.agents.domain.economics.economics import economics_team
from src.model_schemas.schemas import EconomicAnalysisReport

economic_supervisor = create_supervisor(
    model=model,
    agents=economics_team,
    prompt=load_supervisor_prompt('economic_supervisor'),
    response_format= EconomicAnalysisReport
).compile( name="economic_supervisor")