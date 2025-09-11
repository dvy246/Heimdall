"""
Preprocessing Agents

This module contains agents responsible for preprocessing tasks such as
ticker symbol conversion and company name validation.
"""
from langgraph.prebuilt import create_react_agent
from src.config.settings import model
from src.model_schemas.schemas import TickerResponse
from src.tools.utilities.ticker_conversion import get_ticker_from_name,validate_ticker_symbol
from src.config.looging_config import logger
from src.tools.utilities.extra import search_web,search_web2
from src.tools.utilities.ticker_conversion import convert_company_to_ticker
from src.prompts import load_prompt

# Ticker Conversion Agent
logger.info("Creating ticker conversion agent...")

pre_processing_agent = create_react_agent(
    model=model,
    tools=[search_web, search_web2, get_ticker_from_name, validate_ticker_symbol],
    name="pre_processing_agent",
    response_format=TickerResponse,
    prompt=load_prompt('preprocessing_agent')
)

logger.info("Ticker conversion agent created successfully.")
async def ticker_agent_node(state: HeimdallState) -> Dict:
    """
    Handles the conversion of company name to ticker symbol.
    This node should be called early in the workflow to ensure we have a valid ticker.
    """
    print("--- 🏷️ EXECUTING TICKER AGENT ---")
    
    try:
        company_name = state.get('company_name')
        user_message = state.get('messages', [{}])[-1].content if state.get('messages') else ""
        
        if not company_name:
            # Try to extract company name from user message
            company_name = user_message.split()[0] if user_message else ""
        
        if not company_name:
            return {
                "error": "No company name provided. Please specify a company name.",
                "messages": state.get("messages", []) + [AIMessage(content="Please provide a company name to analyze.", name="ticker_agent")]
            }
        
        # Get the ticker using the existing function
        ticker = await convert_company_to_ticker(company_name)
        
        if ticker:
            print(f"✅ Found ticker {ticker} for {company_name}")
            return {
                "ticker": ticker,
                "company_name": company_name,
                "messages": state.get("messages", []) + [AIMessage(content=f"Found ticker {ticker} for {company_name}", name="ticker_agent")]
            }
        else:
            print(f"❌ Could not find ticker for {company_name}")
            return {
                "error": f"Could not find a valid ticker symbol for {company_name}. Please verify the company name and try again.",
                "messages": state.get("messages", []) + [AIMessage(content=f"Could not find a valid ticker symbol for {company_name}. Please verify the company name and try again.", name="ticker_agent")]
            }
            
    except Exception as e:
        print(f"❌ Error in ticker agent: {e}")
        return {
            "error": f"An error occurred while finding the ticker: {str(e)}",
            "messages": state.get("messages", []) + [AIMessage(content=f"An error occurred: {str(e)}", name="ticker_agent")]
        }