from typing import Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from src.graph.state import HeimdallState
import uuid
from src.tools.Rag.rag import ingest_data_filling
from src.agents.supervisors.risk_supervisor import risk_supervisor
from src.agents.domain.adversarial_gauntlet_agents.compliance import compliance_agent
from langgraph_supervisor import create_supervisor
from src.agents.data_ingestor.data_ingestor import data_ingestor
from src.config.settings import model
from src.tools.Rag.rag import query_data
from src.config.logging_config import logger
import sqlite3
import functools
import os
from src.tools.utilities.extra import run_async_safely
import asyncio
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage

# Define the path for the SQLite database
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DATABASE_NAME = 'heimdall.db'
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)


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

def get_session_query_tool(state: HeimdallState):
    """
    Creates and returns a version of the query_data tool that is bound
    to the session-specific RAG path from the current state.
    """
    rag_path = state['rag_path']
    
    # Create a partial function with the rag_path pre-filled.
    bound_query_data = functools.partial(query_data, rag_path=rag_path)
    
    bound_query_data.tool_name = "query_data"
    bound_query_data.__doc__ = query_data.__doc__
    
    return bound_query_data

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

# Define nodes for the graph
def research_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the research supervisor and updates the state with the research report."""
    logger.info("Executing research_node.")
    try:
        result = research_supervisor.invoke(state)
        return {"research_report": result}
    except Exception as e:
        logger.error(f"Error in research_node: {e}", exc_info=True)
        return {"error": f"Research node failed: {str(e)}"}

def valuation_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the valuation supervisor and updates the state with the valuation report."""
    logger.info("Executing valuation_node.")
    try:
        result = valuation_supervisor.invoke(state)
        return {"valuation_report": result}
    except Exception as e:
        logger.error(f"Error in valuation_node: {e}", exc_info=True)
        return {"error": f"Valuation node failed: {str(e)}"}

def risk_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the risk supervisor and updates the state with the risk report."""
    logger.info("Executing risk_node.")
    try:
        result = risk_supervisor.invoke(state)
        return {"risk_report": result}
    except Exception as e:
        logger.error(f"Error in risk_node: {e}", exc_info=True)
        return {"error": f"Risk node failed: {str(e)}"}

def compliance_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the compliance agent and updates the state with the compliance report."""
    logger.info("Executing compliance_node.")
    try:
        result = compliance_agent.invoke(state)
        return {"compliance_report": result}
    except Exception as e:
        logger.error(f"Error in compliance_node: {e}", exc_info=True)
        return {"error": f"Compliance node failed: {str(e)}"}

def aggregate_reports_node(state: HeimdallState) -> Dict[str, Any]:
    """Aggregates reports from various agents into a single final report."""
    logger.info("Aggregating reports.")
    final_report_parts: List[str] = []
    if state.get("research_report"):
        final_report_parts.append(f"Research Report:\n{state['research_report']}")
    if state.get("valuation_report"):
        final_report_parts.append(f"Valuation Report:\n{state['valuation_report']}")
    if state.get("risk_report"):
        final_report_parts.append(f"Risk Report:\n{state['risk_report']}")
    if state.get("compliance_report"):
        final_report_parts.append(f"Compliance Report:\n{state['compliance_report']}")
    
    aggregated_report = "\n\n".join(final_report_parts)
    logger.info("Reports aggregated successfully.")
    return {"final_report": aggregated_report}

def validate_report_node(state: HeimdallState) -> Dict[str, Any]:
    """Validates the aggregated report and updates the state with a validation report."""
    logger.info("Validating aggregated report.")
    # Placeholder for actual validation logic
    # In a real scenario, this would involve another agent or a set of tools
    # to check for consistency, completeness, and adherence to report standards.
    validation_status = "Validation successful."
    if "error" in state.get("final_report", "").lower(): # Simple check for demonstration
        validation_status = "Validation failed: Report contains errors."
        logger.warning("Report validation failed due to detected errors.")
    
    logger.info(f"Report validation status: {validation_status}")
    return {"validation_report": validation_status}

def human_in_the_loop_node(state: HeimdallState) -> Dict[str, Any]:
    """Placeholder for human review. In a real system, this would pause the workflow."""
    logger.info("Entering human-in-the-loop review stage.")
    # In a real application, this would trigger a notification for a human reviewer
    # and potentially pause the graph until a human action is taken.
    # For now, we'll assume automatic approval for demonstration.
    human_decision = "approved" # Could be "approved" or "revisions_needed"
    logger.info(f"Human-in-the-loop decision: {human_decision}")
    return {"human_review_decision": human_decision}

def main_supervisor_node(state: HeimdallState) -> Dict[str, Any]:
    """Invokes the main supervisor to determine the next action."""
    logger.info("Executing main_supervisor_node.")
    try:
        result = main_supervisor.invoke(state)
        return {"main_supervisor_output": result}
    except Exception as e:
        logger.error(f"Error in main_supervisor_node: {e}", exc_info=True)
        return {"error": f"Main supervisor failed: {str(e)}"}

# Define the graph workflow
workflow = StateGraph(HeimdallState)

# Add nodes
workflow.add_node("research", research_node)
workflow.add_node("valuation", valuation_node)
workflow.add_node("risk", risk_node)
workflow.add_node("compliance", compliance_node)
workflow.add_node("aggregate_reports", aggregate_reports_node)
workflow.add_node("validate_report", validate_report_node)
workflow.add_node("human_in_the_loop", human_in_the_loop_node)
workflow.add_node("main_supervisor", main_supervisor_node)

# Define the entry point
workflow.set_entry_point("main_supervisor")

# Define conditional edges for dynamic routing
workflow.add_conditional_edges(
    "main_supervisor",
    lambda state: state.get("main_supervisor_output", {}).get("next_agent", "END"),
    {
        "research_supervisor": "research",
        "valuation_supervisor": "valuation",
        "risk_supervisor": "risk",
        "compliance_agent": "compliance",
        "aggregate_reports": "aggregate_reports",
        "END": END,
    },
)

workflow.add_edge("research", "main_supervisor")
workflow.add_edge("valuation", "main_supervisor")
workflow.add_edge("risk", "main_supervisor")
workflow.add_edge("compliance", "main_supervisor")

workflow.add_edge("aggregate_reports", "validate_report")
workflow.add_conditional_edges(
    "validate_report",
    lambda state: "human_in_the_loop" if "failed" not in state.get("validation_report", "").lower() else "main_supervisor",
    {
        "human_in_the_loop": "human_in_the_loop",
        "main_supervisor": "main_supervisor", # Route back for revisions
    },
)

workflow.add_conditional_edges(
    "human_in_the_loop",
    lambda state: "END" if state.get("human_review_decision") == "approved" else "main_supervisor",
    {
        "END": END,
        "main_supervisor": "main_supervisor", # Route back for revisions
    },
)

# Compile the graph
graph = workflow.compile(checkpointer=main_memory())