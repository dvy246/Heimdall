from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from src.tools.data_providers.alpha_vantage import advanced_analyst,get_insider_info
from src.tools.Rag.rag import query_data,ingest_data_filling
from src.tools.data_providers.finnhub import get_insiders_sentiment
from src.prompts import load_handoff_prompt

quantitative_analyst = create_react_agent(
    model=model,
    tools=[advanced_analyst],
    name='quantitative_analyst',
    prompt=load_handoff_prompt('quants')
)
# --- Create the New Specialist Insider Agent ---
insider_agent = create_react_agent(
    model=model,
    tools=[get_insider_info, get_insiders_sentiment],
    name='insider_agent',
    prompt=load_handoff_prompt('insider')
)

# This agent is the sole keeper of the Corporate Library.
librarian_agent = create_react_agent(
    model=model,
    tools=[ingest_data_filling, query_data],
    name='librarian_agent',
    prompt=load_handoff_prompt('librarian')
)