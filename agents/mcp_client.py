import concurrent.futures
import asyncio
import json
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

# Single MCP client config — one place that knows where the servers live.
_client = MultiServerMCPClient(
    {
        "hotel": {
            "command": sys.executable,
            "args": ["mcp_servers/hotel_server.py"],
            "transport": "stdio",
        }
    }
)

_tools_cache = None


async def _get_tools():
    global _tools_cache
    if _tools_cache is None:
        _tools_cache = await _client.get_tools()
    return _tools_cache


def _unwrap(result):
    """MCP returns results as text-wrapped envelopes; parse them back to dicts."""
    hotels = []
    for item in result:
        if isinstance(item, dict) and "text" in item:
            try:
                hotels.append(json.loads(item["text"]))
            except Exception:
                hotels.append(item["text"])
        else:
            hotels.append(item)
    return hotels


async def _call_tool_async(tool_name: str, args: dict):
    tools = await _get_tools()
    tool = next(t for t in tools if t.name == tool_name)
    raw = await tool.ainvoke(args)
    return _unwrap(raw)


def call_mcp_tool(tool_name: str, args: dict):
    """Sync wrapper for LangGraph nodes. Runs the async MCP call in a
    separate thread so it doesn't collide with FastAPI's running event loop."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, _call_tool_async(tool_name, args))
        return future.result()