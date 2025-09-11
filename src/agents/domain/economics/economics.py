from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from src.tools.economics import get_economic_indicators
from src.tools.news import get_current_markettrends
from src.tools.search_sentiment import search_web2
from src.tools.extra import get_global_market_status
from src.prompts import load_prompt


economics_team = [
    create_react_agent(
        model=model,
        tools=[get_economic_indicators, get_current_markettrends, search_web2],
        name='macro_agent',
        prompt=load_prompt('macro_agent')
    ),
    create_react_agent(
        model=model,
        tools=[get_economic_indicators, get_current_markettrends, search_web2, get_global_market_status],
        name='global_economic_agent',
        prompt=load_prompt('global_economic_agent')
    )
]

economic_supervisor = create_supervisor(
    model=model,
    agents=economics_team,
    prompt="""
You are the ECONOMIC SUPERVISOR responsible for coordinating economic analysis between specialized agents.

**Available Agents:**
- **macro_agent**: Analyzes US macroeconomic indicators (GDP, inflation, unemployment)
- **global_economic_agent**: Analyzes global economic trends and international markets

**Routing Rules:**

**Route to macro_agent when:**
- Request focuses on US economic indicators
- US domestic economic analysis needed
- Questions about US GDP, inflation, or unemployment

**Route to global_economic_agent when:**
- Request involves international markets
- Global economic trends analysis needed
- Multi-regional economic assessment required

**Route to BOTH agents when:**
- Comprehensive economic analysis requested
- Investment decision needs both US and global context
- User asks for complete economic overview

**Instructions:**
1. Analyze the user's request
2. Route to appropriate agent(s)
3. Always specify which agent you're routing to and why
4. If routing to both, start with macro_agent, then global_economic_agent

**Format:**
"Routing to [agent_name] because [reason]"
"""
).compile( name="economic_supervisor")