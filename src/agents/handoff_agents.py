from src.config.settings import model
from src.tools.rag import ingest_data_filling,query_data
from langgraph.prebuilt import create_react_agent




quantitative_analyst = create_react_agent(
    model=model,
    tools=[advaced_analyst],
    name='quantitative_analyst',
    prompt='''You are a specialist  Quantitative Analyst. Your only job is to use your tool
    to perform a standard quantitative analysis on a stock's performance over a 6-month period.

    You MUST call the `get_analytics_sliding_window` tool with the `range_str` parameter set to "6month".
    
    After getting the data, provide a concise summary of the mean return and the annualized standard deviation (volatility)
    and .'''
)
# --- Create the New Specialist Insider Agent ---
insider_agent = create_react_agent(
    model=model,
    tools=[get_insider_info, get_insiders_sentiment], # Note: get_current_date isn't needed if the tools do it internally
    name='insider_agent',
    prompt='''You are a specialist Insider Trading Analyst. Your job is to provide a concise summary of insider sentiment and recent trading activity for a given company.

    **Your Workflow:**
    1.  First, use the `get_insider_sentiment` tool to get the high-level sentiment score (Positive/Negative/Neutral).
    2.  Next, use the `get_insider_info` tool to get the list of the most recent raw buy/sell transactions.
    3.  Finally, synthesize the information from both tools into a single, concise summary. State the overall sentiment and then list the top 3-5 most significant recent transactions as evidence.
    '''
)


# This agent is the sole keeper of the Corporate Library.
librarian_agent = create_react_agent(
    model=model,
    tools=[ingest_data_filling, query_data],
    name='librarian_agent',
    prompt='''You are the Master Librarian for the Heimdall system. Your sole responsibility is to manage the Corporate Library of indexed financial documents.

    You have two primary tasks:
    1.  **Ingest**: When given a report, you MUST use the `ingest_10k_to_library` tool to save it to the archives.
    2.  **Query**: When asked a specific question, you MUST use the `query_data` tool to find the answer within the archives.

    You do not interpret the information. You only ingest, find, and retrieve it.
    '''
)