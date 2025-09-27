from typing import Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from src.graph.state import HeimdallState
import uuid
from src.tools.Rag.rag import ingest_data_filling
from src.agents.supervisors.domain_supervisors.research_supervisor import research_supervisor
from src.agents.domain.adversarial_gauntlet_agents.compliance import compliance_agent
from langgraph_supervisor import create_supervisor
from src.agents.data_ingestor.data_ingestor import data_ingestor
from src.config.settings import model
from src.agents.strategist.strategist import stratergist_agent
from src.agents.supervisors.adversarial_gauntlet_heads.adversarial_gauntlet_supervisor import adversarial_gauntlet_supervisor
from src.tools.Rag.rag import query_data
from src.config.logging_config import logger
import sqlite3
from src.agents.preprocessing.preprocessing import pre_processing_agent 
import functools
from src.tools.utilities.extra import run_async_safely
import asyncio
from src.agents.supervisors.main_supervisor.main_supervisor import main_supervisor
import os
from src.tools.utilities.ticker_conversion import convert_company_to_ticker
from langgraph.types import Command,Interrupt
from langchain_core.messages import AIMessage,HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage
from src.agents.decision_maker.decision_maker import decision_maker
from src.model_schemas.schemas import DecisionOutput

# Define the path for the SQLite database
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DATABASE_NAME = 'heimdall.db'
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)


def main_memory(database_name: str = DATABASE_NAME, reset: bool = True) -> SqliteSaver:
    """
    Initializes and returns a SQLiteSaver for graph state checkpointing.

    Args:
        database_name (str): Name of the SQLite database file.
        reset (bool): Whether to reset the database if it exists.

    Returns:
        SqliteSaver: Configured SQLite saver for LangGraph checkpointing.

    Raises:
        OSError: If database directory creation fails.
        sqlite3.Error: If database connection fails.
    """
    logger.info(f"Initializing main memory with database: {database_name}")
    try:
        os.makedirs(DATABASE_DIR, exist_ok=True)
        db_path = os.path.join(DATABASE_DIR, database_name)

        if os.path.exists(db_path) and reset:
            logger.warning(f"Resetting database: {db_path}")
            os.remove(db_path)

        conn = sqlite3.connect(db_path, check_same_thread=False)
        logger.info(f"Successfully connected to database: {db_path}")
        return SqliteSaver(conn)
    except OSError as e:
        logger.critical(f"Failed to create data directory for database: {e}", exc_info=True)
        raise
    except sqlite3.Error as e:
        logger.critical(f"SQLite database error during initialization: {e}", exc_info=True)
        raise

logger.info("Ticker conversion agent created successfully.")
async def ticker_agent_node(state: HeimdallState) -> Dict:
    """
    Handles the conversion of company name to ticker symbol.
    This node should be called early in the workflow to ensure we have a valid ticker.
    """
    print("--- 🏷️ EXECUTING TICKER AGENT ---")
    
    try:
        company_name = state.get('company_name', '')
        logger.info('Company name:', company_name)
        while i<4:
            ticker=await pre_processing_agent.ainvoke(input={'messages':{'role':'user','content':f'''convert the following company name to ticker symbol:{company_name}'''}}
            )
            if isinstance(ticker,dict) and 'structured_response' in ticker:
                ticker_output=ticker['structured_response']
                logger.info('ticker output:', ticker_output)
                return {"ticker": ticker_output}
            else:
                i+=1
                continue
    except Exception as e:
        logger.error(f"Error in ticker_agent_node: {e}", exc_info=True)
        return {"error": f"Ticker agent node failed: {str(e)}"}

def liberarian_node(state: HeimdallState) -> Dict[str, Any]:
    ''' 
    fetches the data from sec fillings and it ingests it into a session specific RAG database
    '''
    logger.info("Executing librarian_node: Ingesting foundational documents.")
    ticker = state['ticker']
    rag_path = state['rag_path']
    company_name = state['company_name']

    try:
        logger.info(f'Fetching sec data for the {ticker} of company {company_name} into the path {rag_path}')

        agent_input=f"""Generate a comprehensive due diligence report for {ticker} of company {company_name}
        Perform a deep analysis and provide your final report with the required sections: Executive Summary, Business Model, Financial Health, Risk Assessment, Management's Perspective, and Investment Conclusion.
        Ensure all numerical data is presented in bold. extract 10-K and 10-Q and 8-K filings for {company_name}. and also extract its key sections using ur tool and u have to give an output so i can store into my databse
        """
        filling_text= run_async_safely(data_ingestor(agent_input))
        
        if isinstance(filling_text,dict) and 'messages' in filling_text:
            report_content=filling_text['messages'][-1].content
            logger.info(f'Report generated for {ticker}: \n{report_content}')
        else:
            report_content=str(filling_text)
    
        if "Error:" in report_content or not report_content:
            logger.error('error occured while ingesting data')
            raise ValueError("Failed to retrieve 10-K filing text from sec_edgar_agent.")

        logger.info(f"Ingesting 10-K into RAG at {rag_path}...")
        ingestion_result = ingest_data_filling.invoke({
            "report_text": report_content,
            "ticker": ticker,
            "rag_path": rag_path
        })
        logger.info(f"Ingestion result: {ingestion_result}")

        return {"ingestion_result": ingestion_result}
    except Exception as e:
        logger.error(f"Error in librarian_node: {e}", exc_info=True)
        return {"error": f"Librarian node failed: {str(e)}"}

async def orchestrator_node(state: HeimdallState):
    print("--- 🧠 EXECUTING ORCHESTRATOR ---")
    try:
        ticker = state.get('ticker')
        if not ticker:
            return {'error': 'No ticker symbol found in state. Please ensure the ticker agent has set this value.'}
        
        company_name = state.get('company_name', ticker)
        messages = state.get('messages', [])
        
        # Compose a clear, context-rich prompt for the strategist agent
        strategist_input = {
            'message': (
                f"You are to create a comprehensive, step-by-step mission plan for analyzing {company_name} ({ticker}). "
                f"Consider the latest market context and the following analyst message history:\n\n"
                f"{messages}\n\n"
                "Your plan should be actionable, detailed, and tailored to the current market environment."
            )
        }
        mission_plan_response = await stratergist_agent.ainvoke(strategist_input)
        
        # Extract the mission plan content robustly
        if isinstance(mission_plan_response, dict) and 'messages' in mission_plan_response:
            mission_plan_content = mission_plan_response['messages'][-1].content
        else:
            mission_plan_content = str(mission_plan_response)
        
        state['mission_plan'] = mission_plan_content

        # Add a clear, well-formatted message to the conversation history
        orchestrator_message = AIMessage(
            content=f"📝 **Mission Plan for {company_name} ({ticker})**\n\n{mission_plan_content}",
            name='Orchestrator'
        )
        updated_messages = messages + [orchestrator_message]

        return {
            'mission_plan': mission_plan_content,
            "messages": updated_messages
        }
    except Exception as e:
        print(f"[Orchestrator Error] {e}")
        return {'error': f'An unexpected error occurred in the orchestrator: {e}'}

async def main_supervisor_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the main supervisor to determine the next action."""
    logger.info("Executing main_supervisor_node.")
    try:
        ticker=state.get('ticker')
        company_name=state.get('company_name')
        mission_plan=state.get('mission_plan')
        result = await main_supervisor.ainvoke(input={'messages':HumanMessage(content=f'this is the ticker {ticker} of company {company_name} and the mission plan is {mission_plan} so ur goal it to make a comprehensive report for {ticker} of company {company_name} based on the mission plan provided by the user. please generate a draft report that will be used to iterate over until we reach the final report. use ur own knowledge base to write down the report but dont forget to include the mission plan in your report''')})
        if isinstance(result,dict) and 'messages' in result:
             drafted_report=result['messages'][-1].content
        else:
            drafted_report=str(result)
        return {'draft_report': drafted_report}
    except Exception as e:
        logger.error(f"Error in main_supervisor_node: {e}", exc_info=True)
        return {"error": f"Main supervisor failed: {str(e)}"}

async def advarsarial_gauntlet_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the adversarial gauntlet supervisor to assess the report."""
    logger.info("Executing adversarial_gauntlet_node.")
    try:

def human_in_the_loop_node(state: HeimdallState) -> Dict[str, Any]:
    """Human review node: Presents the report for review and pauses for feedback."""
    logger.info("Entering human-in-the-loop review stage.")
    final_report = state.get("final_report", "No report available.")
    human_decision = "pending"  
    logger.info("Human review pending - workflow paused for input.")
    return {
        "human_review_decision": human_decision,
        "presented_report": final_report
    }

def decision_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the decision maker to evaluate the report and decide on iterations."""
    logger.info("Executing decision_node.")
    try:
        # Prepare input for decision maker, focusing on final_report and other key state
        decision_input = {
            "messages": state.get("messages", []),
            "human_feedback": state.get("human_feedback", ""),
            "loop_count": state.get("loop_count", 0),
            **{k: v for k, v in state.items() if k in ["final_report", "research_report", "valuation_report", "risk_report", "compliance_report", "validation_report"]}
        }
        result = decision_maker.invoke(decision_input)
        
        # Parse the last message content to DecisionOutput
        if result["messages"] and hasattr(result["messages"][-1], "content"):
            content = result["messages"][-1].content
            try:
                decision_output = DecisionOutput.model_validate_json(content)
                updated_loop_count = state.get("loop_count", 0) + 1 if decision_output.iteration_required else state.get("loop_count", 0)
                logger.info(f"Decision made: {decision_output.overall_decision}, Iteration required: {decision_output.iteration_required}, Loop count: {updated_loop_count}")
                return {
                    "decision_output": decision_output.model_dump(),
                    "decision_report": decision_output.model_dump_json(),
                    "loop_count": updated_loop_count
                }
            except Exception as parse_e:
                logger.error(f"Failed to parse decision output: {parse_e}")
                return {"error": f"Decision parsing failed: {str(parse_e)}"}
        else:
            return {"error": "No content in decision maker response"}
    except Exception as e:
        logger.error(f"Error in decision_node: {e}", exc_info=True)
        return {"error": f"Decision node failed: {str(e)}"}

def feedback_integration_node(state: HeimdallState) -> Dict[str, Any]:
    """Placeholder node for integrating human feedback into the report."""
    logger.info("Executing feedback_integration_node: Integrating human feedback (placeholder).")
    if state.get("human_feedback"):
        logger.info(f"Human feedback to integrate: {state['human_feedback']}")
    # The actual merge happens in main.py for this implementation.
    return {"integration_note": "Feedback integration completed (placeholder)"}

def final_delivery_node(state: HeimdallState) -> Dict[str, Any]:
    """Placeholder node for final report delivery."""
    logger.info("Executing final_delivery_node: Delivering final report (placeholder).")
    final_report = state.get("final_report", "No final report available.")
    logger.info(f"Final report prepared for delivery:\n{final_report[:500]}...")  # Log preview
    return {"delivery_status": "Final report delivered"}
