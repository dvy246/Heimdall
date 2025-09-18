import asyncio
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from src.graph.workflow import graph
from src.config.logging_config import logger


async def analyze_company(company_name: str) -> Dict[str, Any]:
    """
    Asynchronously runs the financial analysis for a given company using the Heimdall system.

    Args:
        company_name (str): The name of the company to analyze.

    Returns:
        Dict[str, Any]: Analysis results containing either the final report or error information.

    Raises:
        ValueError: If company_name is empty or None.
    """
    if not company_name or not isinstance(company_name, str):
        raise ValueError("Company name must be a non-empty string")

    logger.info(f"--- 🚀 Starting Heimdall Analysis for: {company_name} ---")

    try:
        initial_state = {
            "company_name": company_name,
            "messages": [HumanMessage(content=f"Generate a full financial intelligence report for {company_name}.")]
        }

        final_result: Dict[str, Any] = {}
        async for step in graph.astream(initial_state, {"recursion_limit": 100}):
            node = list(step.keys())[0]
            logger.info(f"--- Node: {node} ---")
            logger.info(step[node])
            final_result = step

        final_report = final_result.get("final_report", "Analysis complete, but no final report was generated.")
        logger.info("--- ✅ Analysis Complete ---")
        return {"status": "success", "company": company_name, "report": final_report}

    except asyncio.TimeoutError:
        logger.error(f"Analysis timed out for {company_name}")
        return {"status": "error", "message": f"Analysis timed out for {company_name}"}
    except Exception as e:
        logger.error(f"An error occurred during analysis for {company_name}: {e}", exc_info=True)
        return {"status": "error", "message": f"An error occurred during analysis: {str(e)}"}

if __name__ == "__main__":
    # Example of how to run the analysis
    company_to_analyze = "Microsoft"
    
    # Run the async function
    try:
        report = asyncio.run(analyze_company(company_to_analyze))
        logger.info("\\n--- Final Report ---")
        logger.info(report)
    except Exception as e:
        logger.critical(f"A critical error occurred in the main execution block: {e}", exc_info=True)