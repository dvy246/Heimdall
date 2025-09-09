from pathlib import Path
import yaml

def load_prompt(agent_name: str) -> str:
    """Load exact prompt text from YAML file without modifications"""
    prompt_path = Path(__file__).parent / "agents" / "prompts.yaml"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file missing for agent: {agent_name}")
    
    with open(prompt_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return data['agents'][agent_name]['prompt']
