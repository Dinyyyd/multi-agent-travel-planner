import asyncio
import json
import concurrent.futures
from langchain_mcp_adapters.client import MultiServerMCPClient

# Map each tool to the server it lives on
TOOL_TO_SERVER = {
    "get_hotels": "hotel",
    "search_hotel": "hotel",
    "book_hotel": "hotel",
    "get_flights": "flight",
    "search_flights": "flight",
    "book_flight": "flight",
}

ALL_SERVERS = {
    "hotel": {
        "command": "python",
        "args": ["mcp_servers/hotel_server.py"],
        "transport": "stdio",
    },
    "flight": {
        "command": "python",
        "args": ["mcp_servers/flight_server.py"],
        "transport": "stdio",
    },
}


def _unwrap(result):
    items = []
    for item in result:
        if isinstance(item, dict) and "text" in item:
            try:
                items.append(json.loads(item["text"]))
            except (json.JSONDecodeError, TypeError):
                items.append(item)
        else:
            items.append(item)
    return items


async def _call_tool_async(tool_name: str, args: dict):
    server_name = TOOL_TO_SERVER.get(tool_name)
    if not server_name or server_name not in ALL_SERVERS:
        raise ValueError(f"Unknown tool: {tool_name}")

    # Connect ONLY to the server this tool belongs to
    single_server = {server_name: ALL_SERVERS[server_name]}
    client = MultiServerMCPClient(single_server)
    tools = await client.get_tools()
    tool = next(t for t in tools if t.name == tool_name)
    raw = await tool.ainvoke(args)
    return _unwrap(raw)


def call_mcp_tool(tool_name: str, args: dict):
    """Sync wrapper. Returns a friendly error dict if the MCP call fails."""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, _call_tool_async(tool_name, args))
            return future.result(timeout=30)
    except Exception:
        return {"error": True, "message": f"The {tool_name} service is temporarily unavailable. Please try again later."}