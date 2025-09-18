from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.agents.domain.adversarial_gauntlet_agents.validation import fact_checker,evaluator_agent,validator_agent
from src.model_schemas.schemas import ValidationReport
from src.tools.analysis.report_writer_tool import generate_synthesized_report

validation_supervisor = create_supervisor(
    [fact_checker, evaluator_agent, validator_agent],
    model=model,
    prompt=load_supervisor_prompt('validation'),
    response_format=ValidationReport,
    tools=[generate_synthesized_report],
    output_mode="last_message"
).compile(name="validation_supervisor")


