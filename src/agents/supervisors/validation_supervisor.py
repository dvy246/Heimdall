from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.agents.validation.validation import fact_checker, evaluator_agent, validator_agent

validation_supervisor = create_supervisor(
    model=model,
    agents=[fact_checker, evaluator_agent, validator_agent],
    prompt=load_supervisor_prompt('validation'),
    output_mode="last_message"
)