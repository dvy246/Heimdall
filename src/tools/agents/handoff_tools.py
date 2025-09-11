from langchain_core.tools import BaseTool
from src.config.looging_config import logger
from langgraph_supervisor import create_handoff_tool

def create_handoff_tools_agent(name: str) -> BaseTool:
    """Create and return handoff tools for agent delegation.
    
    Args:
        name: Agent name or hint (e.g., 'insider', 'quant', 'librarian')
    
    Returns:
        BaseTool: Handoff tool for the specified agent
    
    Available agents:
    - insider_agent: For insider trading analysis and sentiment evaluation
    - quantitative_analyst: For quantitative analysis and advanced analytics  
    - librarian: For data ingestion or querying from knowledge base
   
    """
    if not name or not isinstance(name, str):
        logger.error(f"Invalid name parameter: {name}. Must be a non-empty string.")
        raise ValueError("Name parameter must be a non-empty string")    
    try:
        name_lower = name.lower().strip()
        
        if any(keyword in name_lower for keyword in ["insider", "trading", "sentiment"]):
            logger.info("Creating handoff tool for insider trading analysis.")
            return create_handoff_tool(
                agent_name="insider_agent",
                description= "Delegate insider trading analysis and sentiment evaluation."
            )
        elif any(keyword in name_lower for keyword in ["quant", "quantitative", "analyst"]):
            logger.info("Creating handoff tool for quantitative analysis.")
            return create_handoff_tool(
                agent_name="quantitative_analyst",
                description="Delegate quantitative analysis and advanced analytics."
            )
        elif any(keyword in name_lower for keyword in ['librarian','library','knowledge_base']):
            logger.info("Creating handoff tool for librarian.")
            return create_handoff_tool(
                agent_name="librarian",
                description="Handoff to librarian for data ingestion or querying."
            )
        else:
            logger.error(f"Unknown agent name: {name}. No matching agent found for keywords in name.")
            raise ValueError(f"Unknown agent name: {name}. Must contain keywords matching available agents.")
    
    except Exception as e:
        logger.error(f"Failed to create handoff tool for {name}: {str(e)}")
        
