from backend.agents.state import AgentState
from backend.agents.research_agent import research_agent_node


async def doc_agent_node(state: AgentState) -> AgentState:
    return await research_agent_node(state)
