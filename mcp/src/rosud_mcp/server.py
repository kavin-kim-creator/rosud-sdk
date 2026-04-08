"""Rosud MCP Server - main entry point"""
import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
)

from .tools import ALL_TOOLS, TOOL_HANDLERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rosud-mcp")

app = Server("rosud-mcp")


@app.list_tools()
async def list_tools(request: ListToolsRequest) -> ListToolsResult:
    """Return the list of available Rosud payment tools."""
    return ListToolsResult(tools=ALL_TOOLS)


@app.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Execute a tool and return the result."""
    tool_name = request.params.name
    arguments = request.params.arguments or {}

    logger.info("Executing tool: %s, params: %s", tool_name, arguments)

    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return CallToolResult(
            content=[],
            isError=True,
        )

    content = await handler(arguments)
    return CallToolResult(content=content)


async def run() -> None:
    """Run the MCP server in stdio mode."""
    logger.info("Rosud MCP Server starting...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main() -> None:
    """Entry point — called from pyproject.toml scripts."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
