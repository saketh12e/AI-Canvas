from backend.agents.state import AgentState
from backend.agents.canvas_agent import canvas_agent_node


async def visualizer_agent_node(state: AgentState) -> AgentState:
    return await canvas_agent_node(state)
