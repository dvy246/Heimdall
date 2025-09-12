from IPython.display import Image, display

# Import workflow components for external access
try:
    from .workflow import main_memory, graph
except ImportError:
    # Fallback for when dependencies are missing
    main_memory = None
    graph = None
from .state import HeimdallState

# Method 1: Use get_graph() method properly
def display_workflow(workflow):
    """Properly display LangGraph workflow"""
    if workflow:
        try:
            # Get the graph representation
            graph = workflow.get_graph()
            
            # Draw the graph and get PNG bytes
            png_bytes = graph.draw_mermaid_png()
            
            # Display the image
            display(Image(png_bytes))
        
        except Exception as e:
            print(f"Could not display graph: {e}")
            
            # Fallback: print text representation
            print("\nWorkflow Structure:")
            print(f"Nodes: {list(graph.nodes.keys())}")
            print(f"Edges: {[(edge.source, edge.target) for edge in graph.edges]}")

    else:
        return "No workflow to display"