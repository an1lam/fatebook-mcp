import logging
import os
import httpx
import fastmcp
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

mcp = fastmcp.FastMCP("Fatebook MCP Server")


@mcp.tool()
async def list_questions(
    apiKey: str = "",
    resolved: bool | None = None,
    unresolved: bool | None = None,
    searchString: str = "",
    limit: int | None = None,
    cursor: str = ""
) -> str:
    """List Fatebook questions with optional filtering"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    params = {"apiKey": api_key}
    
    # Add optional parameters
    if resolved is not None:
        params["resolved"] = resolved
    if unresolved is not None:
        params["unresolved"] = unresolved
    if searchString:
        params["searchString"] = searchString
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://fatebook.io/api/v0/getQuestions",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return f"Questions data: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    logging.info("Starting Fatebook MCP server...")
    mcp.run()
