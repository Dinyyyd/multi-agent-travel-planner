import asyncio
import json
import concurrent.futures
from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_SERVERS = {
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


async def _call_tool_async(tool_name, args):
    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()
    tool = next(t for t in tools if t.name == tool_name)
    raw = await tool.ainvoke(args)
    return _unwrap(raw)


def call_mcp_tool(tool_name, args):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, _call_tool_async(tool_name, args))
        return future.result()
