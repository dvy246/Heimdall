import asyncio
import os
import uuid
import yaml
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
        session_id = str(uuid.uuid4())
        rag_path = os.path.join("data", f"rag_{session_id}")
        initial_state = {
            "company_name": company_name,
            "session_id": session_id,
            "rag_path": rag_path,
            "loop_count": 0,
            "messages": [HumanMessage(content=f"Generate a full financial intelligence report for {company_name}.")]
        }
        config = {"configurable": {"thread_id": session_id}}

        final_result: Dict[str, Any] = {}
        async for step in graph.astream(initial_state, config):
            node = list(step.keys())[0]
            logger.info(f"--- Node: {node} ---")
            chunk = step[node]
            logger.info(chunk)

            if node == "human_in_the_loop":
                current_state = await graph.aget_state(config)
                values = current_state.values
                if values.get("human_review_decision") == "pending":
                    presented_report = values.get("final_report", "No report available.")
                    print("\n" + "="*80)
                    print("🧑 HUMAN REVIEW REQUIRED")
                    print("="*80)
                    print(presented_report)
                    print("\n" + "-"*80)
                    print("Provide feedback in YAML format to revise the report (e.g., section_name: 'new content').")
                    print("Example:")
                    print("  executive_summary: 'This is a revised executive summary.'")
                    print("  risk_assessment: 'A new risk was identified regarding market volatility.'")
                    print("\nPress Enter to approve the report as-is and finalize.")
                    
                    loop = asyncio.get_event_loop()
                    human_input = await loop.run_in_executor(None, input, "> ")
                    
                    state_update = {
                        "human_review_decision": "approved",
                        "applied_feedback": False
                    }

                    if human_input.strip():
                        try:
                            feedback = yaml.safe_load(human_input)
                            if isinstance(feedback, dict) and feedback:
                                # This is a simple replacement logic. A more sophisticated version
                                # could use an agent to merge the feedback intelligently.
                                updated_report = presented_report
                                for key, value in feedback.items():
                                    # Create a regex to find the section header (case-insensitive)
                                    # e.g., "Executive Summary:" or "executive_summary:"
                                    section_title = key.replace('_', ' ').title()
                                    pattern = re.compile(f"^(.*{re.escape(section_title)}.*)$", re.MULTILINE | re.IGNORECASE)
                                    match = pattern.search(updated_report)
                                    
                                    if match:
                                        # Find where the section ends (next section starts or end of doc)
                                        section_start_pos = match.end()
                                        next_section_match = re.search(r"^\w[\w\s]+:", updated_report[section_start_pos:], re.MULTILINE)
                                        
                                        if next_section_match:
                                            section_end_pos = section_start_pos + next_section_match.start()
                                            updated_report = updated_report[:section_start_pos] + "\n" + value + "\n\n" + updated_report[section_end_pos:]
                                        else:
                                            updated_report = updated_report[:section_start_pos] + "\n" + value
                                    else: # Section not found, append it
                                        updated_report += f"\n\n{section_title}:\n{value}"

                                state_update = {
                                    "human_feedback": feedback,
                                    "final_report": updated_report,
                                    "applied_feedback": True,
                                    "human_review_decision": "changes_applied"
                                }
                                logger.info("Human feedback parsed and applied to report.")
                                print("Feedback captured. Resuming workflow to integrate changes.")
                            else:
                                logger.warning("Feedback was not a valid dictionary. Skipping changes.")
                                print("Invalid feedback format. Skipping changes.")
                        except yaml.YAMLError as e:
                            logger.error(f"YAML parsing error: {e}")
                            print(f"Error parsing YAML: {e}. Skipping changes.")
                    else:
                        print("No feedback provided. Approving report and finalizing.")
                    
                    await graph.aupdate_state(config, state_update)
                    logger.info("Workflow resumed after human review.")

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