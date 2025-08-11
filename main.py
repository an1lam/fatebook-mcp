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


@mcp.tool()
async def resolve_question(
    questionId: str,
    resolution: str,
    questionType: str,
    apiKey: str = ""
) -> str:
    """Resolve a Fatebook question with YES/NO/AMBIGUOUS resolution"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    # Validate resolution parameter
    valid_resolutions = ["YES", "NO", "AMBIGUOUS"]
    if resolution not in valid_resolutions:
        return f"Error: resolution must be one of {valid_resolutions}"
    
    data = {
        "questionId": questionId,
        "resolution": resolution,
        "questionType": questionType,
        "apiKey": api_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/resolveQuestion",
                json=data
            )
            response.raise_for_status()
            
            return f"Question resolved successfully: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def create_question(
    title: str,
    resolveBy: str,
    forecast: float,
    apiKey: str = "",
    tags: list[str] | None = None,
    sharePublicly: bool = False,
    shareWithLists: list[str] | None = None,
    shareWithEmail: list[str] | None = None,
    hideForecastsUntil: str | None = None
) -> str:
    """Create a new Fatebook question"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    # Validate forecast parameter
    if not 0 <= forecast <= 1:
        return "Error: forecast must be between 0 and 1"
    
    params = {
        "apiKey": api_key,
        "title": title,
        "resolveBy": resolveBy,
        "forecast": forecast
    }
    
    # Add optional parameters
    if tags is not None:
        params["tags"] = ",".join(tags)
    if sharePublicly:
        params["sharePublicly"] = sharePublicly
    if shareWithLists is not None:
        params["shareWithLists"] = ",".join(shareWithLists)
    if shareWithEmail is not None:
        params["shareWithEmail"] = ",".join(shareWithEmail)
    if hideForecastsUntil is not None:
        params["hideForecastsUntil"] = hideForecastsUntil
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/createQuestion",
                params=params
            )
            response.raise_for_status()
            
            return f"Question created successfully: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    logging.info("Starting Fatebook MCP server...")
    mcp.run()
