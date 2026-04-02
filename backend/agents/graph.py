from langgraph.graph import StateGraph, START, END

from backend.agents.state import AgentState
from backend.agents.canvas_agent import canvas_agent_node
from backend.agents.explainer_agent import synthesis_agent_node
from backend.agents.planner_agent import planner_agent_node
from backend.agents.research_agent import research_agent_node


def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)

    graph.add_node("planner_agent", planner_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("synthesis_agent", synthesis_agent_node)
    graph.add_node("canvas_agent", canvas_agent_node)

    graph.add_edge(START, "planner_agent")
    graph.add_edge("planner_agent", "research_agent")
    graph.add_edge("research_agent", "synthesis_agent")
    graph.add_edge("synthesis_agent", "canvas_agent")
    graph.add_edge("canvas_agent", END)

    return graph.compile(checkpointer=checkpointer)
