from langgraph.graph import StateGraph, END
from src.graph.state import HeimdallState
from src.graph.nodes import (
    liberarian_node,
    research_node,
    valuation_node,
    risk_node,
    compliance_node,
    aggregate_reports_node,
    validate_report_node,
    decision_node,
    human_in_the_loop_node,
    main_supervisor_node,
    feedback_integration_node,
    final_delivery_node,
    main_memory,
)

workflow = StateGraph(HeimdallState)

# Add nodes
workflow.add_node("librarian", liberarian_node)
workflow.add_node("research", research_node)
workflow.add_node("valuation", valuation_node)
workflow.add_node("risk", risk_node)
workflow.add_node("compliance", compliance_node)
workflow.add_node("aggregate_reports", aggregate_reports_node)
workflow.add_node("validate_report", validate_report_node)
workflow.add_node("decision", decision_node)
workflow.add_node("human_in_the_loop", human_in_the_loop_node)
workflow.add_node("main_supervisor", main_supervisor_node)
workflow.add_node("feedback_integration", feedback_integration_node)
workflow.add_node("final_delivery", final_delivery_node)

# Define the entry point
workflow.set_entry_point("librarian")

# Define conditional edges for dynamic routing
workflow.add_edge("librarian", "main_supervisor")
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
workflow.add_edge("validate_report", "decision")
workflow.add_conditional_edges(
    "decision",
    lambda state: "human_in_the_loop"
    if not state.get("decision_output", {}).get("iteration_required", False)
    or state.get("loop_count", 0) >= 3
    else "main_supervisor",
    {
        "main_supervisor": "main_supervisor",
        "human_in_the_loop": "human_in_the_loop",
    },
)

workflow.add_conditional_edges(
    "human_in_the_loop",
    {
        "feedback_integration": "feedback_integration",
        "final_delivery": "final_delivery",
    },
)

workflow.add_edge("feedback_integration", "final_delivery")
workflow.add_edge("final_delivery", END)

# Compile the graph
graph = workflow.compile(checkpointer=main_memory())