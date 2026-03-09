"""Rosud MCP Server - 메인 진입점"""
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
    """사용 가능한 Rosud 결제 도구 목록을 반환합니다."""
    return ListToolsResult(tools=ALL_TOOLS)


@app.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """도구를 실행하고 결과를 반환합니다."""
    tool_name = request.params.name
    arguments = request.params.arguments or {}

    logger.info("도구 실행: %s, 파라미터: %s", tool_name, arguments)

    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return CallToolResult(
            content=[],
            isError=True,
        )

    content = await handler(arguments)
    return CallToolResult(content=content)


async def run() -> None:
    """MCP 서버를 stdio 모드로 실행합니다."""
    logger.info("Rosud MCP Server 시작...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main() -> None:
    """엔트리포인트 - pyproject.toml scripts에서 호출됩니다."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
