from src.config.settings import model
from src.model_schemas.schemas import Validate,Sector
from src.config.looging_config import logger

# Create structured output models for validation and sector analysis
try:
    model_y_n = model.with_structured_output(Validate)
    logger.info("Successfully created validation model with structured output")
except Exception as e:
    logger.error(f"Failed to create validation model: {e}")
    raise

try:
    sector_model = model.with_structured_output(Sector)
    logger.info("Successfully created sector model with structured output")
except Exception as e:
    logger.error(f"Failed to create sector model: {e}")
    raise