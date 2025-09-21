from langgraph.prebuilt import create_react_agent
from src.config.settings import model
from src.tools.data_providers.financialdatasetsai import interest
from langchain_core.messages import HumanMessage

async def main():
    tool=await interest.fetch_bank_interest_rates()
    return tool

interest_rates_agent = create_react_agent(
    model=model,
    tools=[main()],
    name='interest_rates_agent',
    prompt='Please provide the interest rates'
)

interest_rates_agent.invoke('messages':[HumanMessage(content="Get historical interest rates for Bank of America from 2024-01-01 to 2024-03-0")])