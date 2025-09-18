from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.agents.domain.economics.economics import economics_team
from src.model_schemas.schemas import EconomicAnalysisReport
from src.tools.analysis.report_writer_tool import generate_synthesized_report

economic_supervisor = create_supervisor(
    model=model,
    agents=economics_team,
    prompt=load_supervisor_prompt('economic_supervisor'),
    response_format= EconomicAnalysisReport,
    tools=[generate_synthesized_report],
    output_mode="last_message"
).compile( name="economic_supervisor")