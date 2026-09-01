"""The research graph.

Deliberately mixed. The topology is fully readable, including both
branches of the router. One tool binding is not: the publish step builds
its tools from the environment at runtime, and that step is the one
holding credentials.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_community.tools import TavilySearchResults

from publish import build_publish_tools


def plan_step(state: dict) -> dict:
    return state


def write_step(state: dict) -> dict:
    return state


def route(state: dict) -> str:
    """Runtime routing. ControlLoop cannot know which branch is taken,
    so it must treat both as reachable."""

    return "research" if state.get("needs_sources") else "write"


builder = StateGraph(dict)
builder.add_node("plan", plan_step)
builder.add_node("research", ToolNode([TavilySearchResults()]))
builder.add_node("write", write_step)
# NOT statically resolvable, and deliberately so.
builder.add_node("publish", ToolNode(build_publish_tools()))

builder.add_edge(START, "plan")
builder.add_conditional_edges(
    "plan", route, {"research": "research", "write": "write"}
)
builder.add_edge("research", "write")
builder.add_edge("write", "publish")
builder.add_edge("publish", END)

graph = builder.compile()
