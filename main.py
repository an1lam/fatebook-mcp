import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

from models import Question, QuestionReference, QuestionsList, QuestionsResponse

load_dotenv()

mcp = FastMCP("Fatebook MCP Server")


# Type alias for httpx params to handle mypy type checking
ParamsType = dict[str, str | int | float | bool | None]


@mcp.tool()
async def list_questions(
    ctx: Context,
    apiKey: str = "",
    resolved: bool = False,
    unresolved: bool = False,
    searchString: str = "",
    limit: int = 100,
    cursor: str = "",
    detailed: bool = False,
) -> QuestionsList:
    """List Fatebook questions with optional filtering

    Returns a list of Question objects. By default returns core fields only.
    Set detailed=True to include all available fields (forecasts, comments, etc.).
    """

    await ctx.info(
        f"list_questions called with resolved={resolved}, unresolved={unresolved}, searchString='{searchString}', limit={limit}, detailed={detailed}"
    )

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        await ctx.error("API key is required but not provided")
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

    params: dict[str, Any] = {"apiKey": api_key}

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
            response = await client.get("https://fatebook.io/api/v0/getQuestions", params=params)
            response.raise_for_status()

            data = response.json()

            # Parse response using Pydantic model
            questions_response = QuestionsResponse(**data)
            questions = questions_response.items

            await ctx.info(f"Successfully retrieved {len(questions)} questions")

            # Return as QuestionsList with 'result' field to match MCP schema expectations
            return QuestionsList(result=questions)

    except httpx.HTTPError as e:
        await ctx.error(f"HTTP error occurred: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error occurred: {e}")
        raise


@mcp.tool()
async def get_question(ctx: Context, questionId: str, apiKey: str = "") -> Question:
    """Get detailed information about a specific Fatebook question

    Returns a structured Question object with all available fields.
    """

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        await ctx.error("API key is required but not provided")
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

    params: ParamsType = {"apiKey": api_key, "questionId": questionId}

    await ctx.debug(f"Making API request for question {questionId}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://fatebook.io/api/v0/getQuestion", params=params)
            response.raise_for_status()

            question_data = response.json()
            await ctx.info(f"Successfully retrieved question {questionId}")

            # Add the ID to the data since the API doesn't return it
            question_data["id"] = questionId

            # Parse as Question model and return it
            question = Question(**question_data)
            return question

    except httpx.HTTPError as e:
        await ctx.error(f"HTTP error occurred: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error occurred: {e}")
        raise


@mcp.tool()
async def resolve_question(
    questionId: str, resolution: str, questionType: str, apiKey: str = ""
) -> bool:
    """Resolve a Fatebook question with YES/NO/AMBIGUOUS resolution"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

    # Validate resolution parameter
    valid_resolutions = ["YES", "NO", "AMBIGUOUS"]
    if resolution not in valid_resolutions:
        raise ValueError(f"resolution must be one of {valid_resolutions}")

    data = {
        "questionId": questionId,
        "resolution": resolution,
        "questionType": questionType,
        "apiKey": api_key,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://fatebook.io/api/v0/resolveQuestion", json=data)
            response.raise_for_status()
            return True

    except httpx.HTTPError:
        raise
    except Exception:
        raise


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
) -> QuestionReference:
    """Create a new Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

    # Validate forecast parameter
    if not 0 <= forecast <= 1:
        raise ValueError("forecast must be between 0 and 1")

    params: ParamsType = {
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
            response = await client.post("https://fatebook.io/api/v0/createQuestion", params=params)
            response.raise_for_status()

            # Parse the URL from the response to extract title and ID
            url = response.text.strip()
            if url.startswith("https://fatebook.io/q/"):
                # Extract the slug part after /q/
                slug = url.replace("https://fatebook.io/q/", "")

                # Split on the last occurrence of -- to separate title and ID
                if "--" in slug:
                    url_title, question_id = slug.rsplit("--", 1)
                    return QuestionReference(id=question_id, title=title)
                else:
                    raise ValueError(f"Could not parse question ID from URL: {url}")
            else:
                raise ValueError(f"Unexpected response format: {url}")

    except httpx.HTTPError:
        raise
    except Exception:
        raise


@mcp.tool()
async def add_forecast(
    questionId: str, forecast: float, apiKey: str = "", optionId: str = ""
) -> bool:
    """Add a forecast to a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

    # Validate forecast parameter
    if not 0 <= forecast <= 1:
        raise ValueError("forecast must be between 0 and 1")

    data = {"questionId": questionId, "forecast": forecast, "apiKey": api_key}

    # Add optional parameter for multi-choice questions
    if optionId:
        data["optionId"] = optionId

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://fatebook.io/api/v0/addForecast", json=data)
            response.raise_for_status()
            return True

    except httpx.HTTPError:
        raise
    except Exception:
        raise


@mcp.tool()
async def add_comment(questionId: str, comment: str, apiKey: str = "") -> bool:
    """Add a comment to a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

    data = {"questionId": questionId, "comment": comment, "apiKey": api_key}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://fatebook.io/api/v0/addComment", json=data)
            response.raise_for_status()
            return True

    except httpx.HTTPError:
        raise
    except Exception:
        raise


@mcp.tool()
async def delete_question(questionId: str, apiKey: str = "") -> bool:
    """Delete a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

    params = {"questionId": questionId, "apiKey": api_key}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                "https://fatebook.io/api/v0/deleteQuestion", params=params
            )
            response.raise_for_status()
            return True

    except httpx.HTTPError:
        raise
    except Exception:
        raise


@mcp.tool()
async def edit_question(
    questionId: str,
    apiKey: str = "",
    title: str = "",
    resolveBy: str = "",
    notes: str = "",
) -> bool:
    """Edit a Fatebook question"""

    api_key = apiKey or os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        raise ValueError(
            "API key is required (provide as parameter or set FATEBOOK_API_KEY environment variable)"
        )

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
            response = await client.patch("https://fatebook.io/api/v0/editQuestion", json=data)
            response.raise_for_status()
            return True

    except httpx.HTTPError:
        raise
    except Exception:
        raise


@mcp.tool()
async def count_forecasts(userId: str) -> int:
    """Count forecasts for a specific user"""

    params = {"userId": userId}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://fatebook.io/api/v0/countForecasts", params=params)
            response.raise_for_status()

            # Parse JSON response and return the count
            data = response.json()
            return int(data.get("count", 0))

    except httpx.HTTPError:
        raise
    except Exception:
        raise


if __name__ == "__main__":
    mcp.run()
