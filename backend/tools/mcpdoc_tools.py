from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_CONFIG = {
    "langchain-docs": {
        "command": "uvx",
        "args": [
            "--from", "mcpdoc", "mcpdoc",
            "--urls",
            "LangChain:https://python.langchain.com/llms.txt",
            "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt",
            "LangSmith:https://docs.smith.langchain.com/llms.txt",
            "--transport", "stdio"
        ],
        "transport": "stdio"
    }
}

# Global client and cached tools — initialized once at app startup via lifespan
mcp_client: MultiServerMCPClient | None = None
_cached_tools: list | None = None


async def init_mcp_client() -> MultiServerMCPClient:
    """Create MCP client and eagerly fetch tools so the subprocess starts once.
    Called once in FastAPI lifespan — NOT per request."""
    global mcp_client, _cached_tools
    mcp_client = MultiServerMCPClient(MCP_CONFIG)
    # get_tools() starts the subprocess and loads tool definitions
    _cached_tools = await mcp_client.get_tools()
    return mcp_client


async def shutdown_mcp_client() -> None:
    """Clean up MCP client on app shutdown."""
    global mcp_client, _cached_tools
    mcp_client = None
    _cached_tools = None


def get_mcp_tools() -> list:
    """Return cached LangChain tool objects for list_doc_sources and fetch_docs."""
    if _cached_tools is None:
        raise RuntimeError("MCP client not initialized. Call init_mcp_client() first.")
    return _cached_tools
