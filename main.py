import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server

logging.basicConfig(level=logging.INFO)


app = Server("fatebook-mcp")


@app.list_tools()
async def list_tools():
    return []


@app.call_tool()
async def call_tool(name, arguments):
    pass


async def main():
    logging.info("Starting Fatebook MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        logging.info("Server running and ready for connections")
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
