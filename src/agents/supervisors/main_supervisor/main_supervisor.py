# Create the main supervisor
from src.agents.supervisors.domain_supervisors.research_supervisor import research_supervisor
from src.agents.supervisors.domain_supervisors.valuation_supervisor import valuation_supervisor
from src.agents.supervisors.domain_supervisors.risk_supervisor import risk_supervisor
from src.agents.supervisors.domain_supervisors.business_supervisor import business_operations_supervisor
from src.agents.supervisors.adversarial_gauntlet_heads.adversarial_gauntlet_supervisor import adversarial_gauntlet_supervisor
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from src.prompts import load_supervisor_prompt

logger.info("Creating main supervisor...")

all_supervisors = [
    research_supervisor,
    valuation_supervisor,
    risk_supervisor,
    business_operations_supervisor,
]

main_supervisor = create_supervisor(
    all_supervisors,
    prompt=load_supervisor_prompt('main_supervisor'),
    output_mode="last_message",
    model=model
).compile(name='main_supervisor')

logger.info("Main supervisor created successfully.")