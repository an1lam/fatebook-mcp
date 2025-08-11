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


@mcp.tool()
async def add_forecast(
    questionId: str,
    forecast: float,
    apiKey: str = "",
    optionId: str | None = None
) -> str:
    """Add a forecast to a Fatebook question"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    # Validate forecast parameter
    if not 0 <= forecast <= 1:
        return "Error: forecast must be between 0 and 1"
    
    data = {
        "questionId": questionId,
        "forecast": forecast,
        "apiKey": api_key
    }
    
    # Add optional parameter for multi-choice questions
    if optionId is not None:
        data["optionId"] = optionId
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/addForecast",
                json=data
            )
            response.raise_for_status()
            
            return f"Forecast added successfully: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def add_comment(
    questionId: str,
    comment: str,
    apiKey: str = ""
) -> str:
    """Add a comment to a Fatebook question"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    data = {
        "questionId": questionId,
        "comment": comment,
        "apiKey": api_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/addComment",
                json=data
            )
            response.raise_for_status()
            
            return f"Comment added successfully: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def delete_question(
    questionId: str,
    apiKey: str = ""
) -> str:
    """Delete a Fatebook question"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    params = {
        "questionId": questionId,
        "apiKey": api_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                "https://fatebook.io/api/v0/deleteQuestion",
                params=params
            )
            response.raise_for_status()
            
            return f"Question deleted successfully: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def edit_question(
    questionId: str,
    apiKey: str = "",
    title: str | None = None,
    resolveBy: str | None = None,
    notes: str | None = None
) -> str:
    """Edit a Fatebook question"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    data = {
        "questionId": questionId,
        "apiKey": api_key
    }
    
    # Add optional parameters only if provided
    if title is not None:
        data["title"] = title
    if resolveBy is not None:
        data["resolveBy"] = resolveBy
    if notes is not None:
        data["notes"] = notes
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                "https://fatebook.io/api/v0/editQuestion",
                json=data
            )
            response.raise_for_status()
            
            return f"Question edited successfully: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def count_forecasts(
    userId: str
) -> str:
    """Count forecasts for a specific user"""
    
    params = {
        "userId": userId
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://fatebook.io/api/v0/countForecasts",
                params=params
            )
            response.raise_for_status()
            
            return f"Forecast count data: {response.text}"
            
    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    logging.info("Starting Fatebook MCP server...")
    mcp.run()
