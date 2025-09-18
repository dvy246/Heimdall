from langchain_core.tools import tool
from src.config.logging_config import logger
from src.agents.report_writer.report_writer import report_writer

@tool(description='Generate a synthesized financial report from raw analytical data using the report writer agent')
def generate_synthesized_report(raw_data: str, ticker: str, analysis_type: str) -> str:
    """
    Generate a professional, synthesized financial report from raw analytical data.

    Args:
        raw_data (str): The raw analytical data, findings, and research notes to synthesize
        ticker (str): The stock ticker symbol for the company
        analysis_type (str): The type of analysis (e.g., 'research', 'valuation', 'risk', 'business','financial','economics')

    Returns:
        str: A polished, investment-grade financial report
    """
    logger.info(f"Generating synthesized {analysis_type} report for {ticker}")

    try:
        # Create the input message for the report writer agent
        user_message = f"""
        Please synthesize the following raw {analysis_type} data into a professional financial report for {ticker}:

        RAW DATA:
        {raw_data}

        ANALYSIS TYPE: {analysis_type}
        COMPANY TICKER: {ticker}

        Please create a comprehensive, evidence-based report that meets institutional standards.
        """

        # Invoke the report writer agent
        result = report_writer.invoke({"messages": [{"role": "user", "content": user_message}]})

        # Extract the final response from the agent
        final_response = result["messages"][-1].content

        return final_response

    except Exception as e:
        logger.error(f"Error generating synthesized report: {e}")
        return f"Error generating synthesized report: {e}"
