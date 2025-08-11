import os
import httpx
from enum import Enum
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Fatebook MCP Server")


class QuestionFormat(Enum):
    SHORT = "short"
    DETAILED = "detailed"


def format_question(question: dict, format: QuestionFormat) -> str:
    """Format a Fatebook question for display"""
    
    if format == QuestionFormat.SHORT:
        # Short format for lists
        status = "✅ RESOLVED" if question.get("resolved") else "⏳ OPEN"
        resolution = f" ({question.get('resolution', 'N/A')})" if question.get("resolved") else ""
        forecast_count = len(question.get("forecasts", []))
        forecast_text = f" | {forecast_count} forecast{'s' if forecast_count != 1 else ''}"
        tags = ", ".join([tag["name"] for tag in question.get("tags", [])])
        tags_text = f" | Tags: {tags}" if tags else ""
        
        return f"**{question.get('title', 'N/A')}**\n{status}{resolution} | ID: {question.get('id', 'N/A')}{forecast_text}{tags_text}"
    
    elif format == QuestionFormat.DETAILED:
        # Detailed format for single questions
        lines = []
        lines.append(f"**{question.get('title', 'N/A')}**")
        lines.append(f"ID: {question.get('id', 'N/A')}")
        lines.append(f"Type: {question.get('type', 'N/A')}")
        lines.append(f"Created: {question.get('createdAt', 'N/A')}")
        lines.append(f"Resolve By: {question.get('resolveBy', 'N/A')}")
        
        status = "✅ Resolved" if question.get("resolved") else "⏳ Open"
        if question.get("resolved"):
            status += f" as {question.get('resolution', 'N/A')} on {question.get('resolvedAt', 'N/A')}"
        lines.append(f"Status: {status}")
        
        if question.get("notes"):
            lines.append(f"Notes: {question.get('notes')}")
        
        # Forecasts
        forecasts = question.get("forecasts", [])
        if forecasts:
            lines.append(f"Forecasts ({len(forecasts)}):")
            for forecast in forecasts:
                forecast_val = float(forecast.get("forecast", 0))
                user_name = forecast.get("user", {}).get("name", "Unknown")
                lines.append(f"  • {user_name}: {forecast_val:.0%}")
        
        # Tags
        tags = question.get("tags", [])
        if tags:
            tag_names = [tag["name"] for tag in tags]
            lines.append(f"Tags: {', '.join(tag_names)}")
        
        # Comments
        comments = question.get("comments", [])
        if comments:
            lines.append(f"Comments ({len(comments)}):")
            for comment in comments:
                user_name = comment.get("user", {}).get("name", "Unknown")
                comment_text = comment.get("comment", "")
                lines.append(f"  • {user_name}: {comment_text}")
        
        # Visibility
        visibility = []
        if question.get("sharedPublicly"):
            visibility.append("Public")
        if question.get("unlisted"):
            visibility.append("Unlisted")
        if visibility:
            lines.append(f"Visibility: {', '.join(visibility)}")
        
        return "\n".join(lines)
    
    else:
        return f"Unknown format: {format}"


@mcp.tool()
async def list_questions(
    ctx: Context,
    apiKey: str = "",
    resolved: bool = False,
    unresolved: bool = False,
    searchString: str = "",
    limit: int = 100,
    cursor: str = "",
) -> str:
    """List Fatebook questions with optional filtering"""

    await ctx.info(
        f"list_questions called with resolved={resolved}, unresolved={unresolved}, searchString='{searchString}', limit={limit}"
    )

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        await ctx.error("API key is required but not provided")
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"

    params = {"apiKey": api_key}

    # Add optional parameters
    if resolved:
        params["resolved"] = resolved
    if unresolved:
        params["unresolved"] = unresolved
    if searchString:
        params["searchString"] = searchString
    params["limit"] = limit
    if cursor:
        params["cursor"] = cursor

    await ctx.debug(f"Making API request with params: {params}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://fatebook.io/api/v0/getQuestions", params=params
            )
            response.raise_for_status()

            data = response.json()
            questions = data.get('items', [])  # Based on the example data structure
            await ctx.info(
                f"Successfully retrieved {len(questions)} questions"
            )
            
            if not questions:
                return "No questions found."
            
            formatted_questions = []
            for question in questions:
                formatted_questions.append(format_question(question, QuestionFormat.SHORT))
            
            return "\n\n".join(formatted_questions)

    except httpx.HTTPError as e:
        await ctx.error(f"HTTP error occurred: {e}")
        return f"HTTP error: {e}"
    except Exception as e:
        await ctx.error(f"Unexpected error occurred: {e}")
        return f"Error: {e}"


@mcp.tool()
async def get_question(ctx: Context, questionId: str, apiKey: str = "") -> str:
    """Get detailed information about a specific Fatebook question"""
    
    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        await ctx.error("API key is required but not provided")
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
    
    params = {"apiKey": api_key, "questionId": questionId}
    
    await ctx.debug(f"Making API request for question {questionId}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://fatebook.io/api/v0/getQuestion", params=params
            )
            response.raise_for_status()
            
            question = response.json()
            await ctx.info(f"Successfully retrieved question {questionId}")
            
            return format_question(question, QuestionFormat.DETAILED)
    
    except httpx.HTTPError as e:
        await ctx.error(f"HTTP error occurred: {e}")
        return f"HTTP error: {e}"
    except Exception as e:
        await ctx.error(f"Unexpected error occurred: {e}")
        return f"Error: {e}"


@mcp.tool()
async def resolve_question(
    questionId: str, resolution: str, questionType: str, apiKey: str = ""
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
        "apiKey": api_key,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/resolveQuestion", json=data
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
    tags: list[str] = [],
    sharePublicly: bool = False,
    shareWithLists: list[str] = [],
    shareWithEmail: list[str] = [],
    hideForecastsUntil: str = "",
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
        "forecast": forecast,
    }

    # Add optional parameters
    if tags:
        params["tags"] = ",".join(tags)
    if sharePublicly:
        params["sharePublicly"] = sharePublicly
    if shareWithLists:
        params["shareWithLists"] = ",".join(shareWithLists)
    if shareWithEmail:
        params["shareWithEmail"] = ",".join(shareWithEmail)
    if hideForecastsUntil:
        params["hideForecastsUntil"] = hideForecastsUntil

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/createQuestion", params=params
            )
            response.raise_for_status()

            # Parse the URL from the response to extract title and ID
            url = response.text.strip()
            if url.startswith("https://fatebook.io/q/"):
                # Extract the slug part after /q/
                slug = url.replace("https://fatebook.io/q/", "")
                
                # Split on the last occurrence of -- to separate title and ID
                if "--" in slug:
                    url_title, question_id = slug.rsplit("--", 1)
                    
                    return f"**Question Created Successfully!**\nTitle: {title}\nID: {question_id}\nURL: {url}"
                else:
                    return f"**Question Created Successfully!**\nTitle: {title}\nURL: {url}\n(Could not parse question ID from URL format)"
            else:
                return f"**Question Created Successfully!**\nTitle: {title}\nResponse: {url}"

    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def add_forecast(
    questionId: str, forecast: float, apiKey: str = "", optionId: str = ""
) -> str:
    """Add a forecast to a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"

    # Validate forecast parameter
    if not 0 <= forecast <= 1:
        return "Error: forecast must be between 0 and 1"

    data = {"questionId": questionId, "forecast": forecast, "apiKey": api_key}

    # Add optional parameter for multi-choice questions
    if optionId:
        data["optionId"] = optionId

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/addForecast", json=data
            )
            response.raise_for_status()

            return f"Forecast added successfully: {response.text}"

    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def add_comment(questionId: str, comment: str, apiKey: str = "") -> str:
    """Add a comment to a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"

    data = {"questionId": questionId, "comment": comment, "apiKey": api_key}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fatebook.io/api/v0/addComment", json=data
            )
            response.raise_for_status()

            return f"Comment added successfully: {response.text}"

    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def delete_question(questionId: str, apiKey: str = "") -> str:
    """Delete a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"

    params = {"questionId": questionId, "apiKey": api_key}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                "https://fatebook.io/api/v0/deleteQuestion", params=params
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
    title: str = "",
    resolveBy: str = "",
    notes: str = "",
) -> str:
    """Edit a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        return "Error: API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"

    data = {"questionId": questionId, "apiKey": api_key}

    # Add optional parameters only if provided
    if title:
        data["title"] = title
    if resolveBy:
        data["resolveBy"] = resolveBy
    if notes:
        data["notes"] = notes

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                "https://fatebook.io/api/v0/editQuestion", json=data
            )
            response.raise_for_status()

            return f"Question edited successfully: {response.text}"

    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def count_forecasts(userId: str) -> str:
    """Count forecasts for a specific user"""

    params = {"userId": userId}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://fatebook.io/api/v0/countForecasts", params=params
            )
            response.raise_for_status()

            return f"Forecast count data: {response.text}"

    except httpx.HTTPError as e:
        return f"HTTP error: {e}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
