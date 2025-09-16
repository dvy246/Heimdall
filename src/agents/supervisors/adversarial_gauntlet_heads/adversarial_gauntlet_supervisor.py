from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from src.agents.supervisors.adversarial_gauntlet_heads.validation_supervisor import validation_supervisor
from src.agents.domain.adversarial_gauntlet_agents.compliance import compliance_agent
from src.agents.domain.adversarial_gauntlet_agents.socratic import socratic_agent
from src.model_schemas.schemas import ValidationReport

logger.info("Creating adversarial gauntlet supervisor...")

adversarial_gauntlet_supervisor = create_supervisor(
    [validation_supervisor, compliance_agent, socratic_agent],
    model=model,
    prompt=load_supervisor_prompt('adversarial_gauntlet'),
    response_format=ValidationReport,
    output_mode="last_message"
).compile(name="adversarial_gauntlet_supervisor")

logger.info("Adversarial gauntlet supervisor created successfully.")
