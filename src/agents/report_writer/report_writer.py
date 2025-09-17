from langgraph.prebuilt import create_react_agent
from src.config.settings import model
from src.config.logging_config import logger
from src.tools.Rag.rag import query_data
from src.prompts import load_prompt

logger.info("Creating report writer agent...")
report_writer=create_react_agent(
    model=model,
    prompt=load_prompt('report_writer_agent'),
    tools=[query_data]
)