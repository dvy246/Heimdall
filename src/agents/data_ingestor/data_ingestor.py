from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from src.tools.data_providers.sec_fillings_data import (
    fetch_sec_filings,
    fetch_sec_company_data,
    fetch_multiple_sec_filings,
    extract_key_sections,
)
from src.prompts import load_prompt
from langchain_core.messages import HumanMessage

sec_edgar_agent = create_react_agent(
    model=model,
    tools=[fetch_sec_filings, fetch_sec_company_data, fetch_multiple_sec_filings, extract_key_sections],
    name='sec_edgar_agent',
    prompt=load_prompt('sec_edgar_agent')
)

async def data_ingestor(input:str):
     result=await sec_edgar_agent.ainvoke(
        input={'messages':HumanMessage(content=input)}
    )
     return result