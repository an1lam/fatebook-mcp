#!/usr/bin/env python3
"""
Pytest-based integration tests for the Fatebook MCP server.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import pytest
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent
from typing_extensions import AsyncGenerator

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_API_KEY = os.getenv("FATEBOOK_API_KEY")
if TEST_API_KEY is None:
    raise ValueError(
        "Need FATEBOOK_API_KEY env variable to be set either in .env or the local environment"
    )

# Test user ID for count forecasts testing (from the test API key user)
TEST_USER_ID = "cme6dxa8g0001i7g74q4exorm"


async def call_tool_and_check_content(
    session: ClientSession, tool_name: str, **tool_args: Any
) -> str | None:
    """Helper function to call a tool and return its content, handling common error cases."""
    try:
        tool_result = await session.call_tool(tool_name, tool_args)
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        raise

    if not tool_result.content:
        logger.warning(f"No content in {tool_name} response")
        return None

    # Check if the first content item is text content
    content_item = tool_result.content[0]

    assert (
        content_item is not None
        and isinstance(content_item, TextContent)
        and hasattr(content_item, "text")
    )
    return content_item.text


@asynccontextmanager
async def create_stdio_mcp_client(
    include_tools: bool = False,
) -> AsyncGenerator[tuple[ClientSession, set[str] | None], None]:
    """Helper function to create an MCP client session connected via stdio - similar to MCP SDK pattern.

    Args:
        include_tools: If True, yields (session, available_tools), otherwise just session
    """
    api_key = os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        raise ValueError("FATEBOOK_API_KEY environment variable is required for testing")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"FATEBOOK_API_KEY": api_key},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            if include_tools:
                tools_response = await session.list_tools()
                available_tools = {tool.name for tool in tools_response.tools}
                yield session, available_tools
            else:
                yield session, None


@pytest.mark.anyio
async def test_count_forecasts():
    """Test the count_forecasts endpoint."""
    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # Verify the tool is available
        assert "count_forecasts" in available_tools, "count_forecasts tool not found"

        # Test counting forecasts for the test user ID
        count_content = await call_tool_and_check_content(
            session, "count_forecasts", userId=TEST_USER_ID
        )

        assert count_content is not None, "No content in count_forecasts response"

        count_value = int(count_content)
        assert count_value >= 0, f"Expected non-negative forecast count, got: {count_value}"


@pytest.mark.anyio
async def test_list_tools():
    """Test listing available tools - demonstrates basic usage pattern."""
    async with create_stdio_mcp_client() as (session, _):
        # Get available tools
        tools_response = await session.list_tools()
        available_tools = {tool.name for tool in tools_response.tools}

        # Verify we have expected Fatebook tools
        expected_tools = {"list_questions", "create_question", "count_forecasts"}
        assert expected_tools.issubset(available_tools), (
            f"Missing tools: {expected_tools - available_tools}"
        )
        assert len(available_tools) > 0, "Should have at least some tools available"


@pytest.mark.anyio
async def test_create_edit_and_resolve_question():
    """Test the full create -> edit -> resolve question flow."""
    from datetime import datetime, timedelta

    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # Verify required tools are available
        required_tools = {"create_question", "edit_question", "resolve_question"}
        assert required_tools.issubset(available_tools), (
            f"Missing tools: {required_tools - available_tools}"
        )

        # Step 1: Create a test question
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        create_content = await call_tool_and_check_content(
            session,
            "create_question",
            title="MCP Edit Test Question",
            resolveBy=resolve_date,
            forecast=0.7,
            apiKey=TEST_API_KEY,
            tags=["test", "edit", "mcp"],
        )

        assert create_content is not None, "No content in create_question response"

        # Parse JSON response to get question ID
        create_data = json.loads(create_content)
        question_id = create_data.get("id")
        title = create_data.get("title")

        assert question_id is not None, "No question ID in response"
        assert title == "MCP Edit Test Question", f"Unexpected title: {title}"

        # Step 2: Edit the question
        new_resolve_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        edit_content = await call_tool_and_check_content(
            session,
            "edit_question",
            questionId=question_id,
            title="MCP Edit Test Question (UPDATED)",
            resolveBy=new_resolve_date,
            notes="This question was updated via MCP integration test",
            apiKey=TEST_API_KEY,
        )

        assert edit_content is not None, "No content in edit_question response"
        assert edit_content.lower() == "true", f"Question editing failed: {edit_content}"

        # Step 3: Resolve the question
        resolve_content = await call_tool_and_check_content(
            session,
            "resolve_question",
            questionId=question_id,
            resolution="AMBIGUOUS",
            questionType="BINARY",
            apiKey=TEST_API_KEY,
        )

        assert resolve_content is not None, "No content in resolve_question response"
        assert resolve_content.lower() == "true", f"Question resolution failed: {resolve_content}"


@pytest.mark.anyio
async def test_create_and_delete_question():
    """Test the full create -> delete question flow."""
    from datetime import datetime, timedelta

    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # Verify required tools are available
        required_tools = {"create_question", "delete_question"}
        assert required_tools.issubset(available_tools), (
            f"Missing tools: {required_tools - available_tools}"
        )

        # Step 1: Create a test question
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        create_content = await call_tool_and_check_content(
            session,
            "create_question",
            title="MCP Delete Test Question",
            resolveBy=resolve_date,
            forecast=0.6,
            apiKey=TEST_API_KEY,
            tags=["test", "delete", "mcp"],
        )

        assert create_content is not None, "No content in create_question response"

        # Parse JSON response to get question ID
        create_data = json.loads(create_content)
        question_id = create_data.get("id")
        title = create_data.get("title")

        assert question_id is not None, "No question ID in response"
        assert title == "MCP Delete Test Question", f"Unexpected title: {title}"

        # Step 2: Delete the question
        delete_content = await call_tool_and_check_content(
            session, "delete_question", questionId=question_id, apiKey=TEST_API_KEY
        )

        assert delete_content is not None, "No content in delete_question response"
        assert delete_content.lower() == "true", f"Question deletion failed: {delete_content}"


@pytest.mark.anyio
async def test_create_and_add_comment_question():
    """Test the full create -> add_comment -> resolve question flow."""
    from datetime import datetime, timedelta

    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # Verify required tools are available
        required_tools = {"create_question", "add_comment", "resolve_question"}
        assert required_tools.issubset(available_tools), (
            f"Missing tools: {required_tools - available_tools}"
        )

        # Step 1: Create a test question
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        create_content = await call_tool_and_check_content(
            session,
            "create_question",
            title="MCP Comment Test Question",
            resolveBy=resolve_date,
            forecast=0.4,
            apiKey=TEST_API_KEY,
            tags=["test", "comment", "mcp"],
        )

        assert create_content is not None, "No content in create_question response"

        # Parse JSON response to get question ID
        create_data = json.loads(create_content)
        question_id = create_data.get("id")
        title = create_data.get("title")

        assert question_id is not None, "No question ID in response"
        assert title == "MCP Comment Test Question", f"Unexpected title: {title}"

        # Step 2: Add a comment to the question
        comment_content = await call_tool_and_check_content(
            session,
            "add_comment",
            questionId=question_id,
            comment="This is a test comment from the MCP integration test",
            apiKey=TEST_API_KEY,
        )

        assert comment_content is not None, "No content in add_comment response"
        assert comment_content.lower() == "true", f"Adding comment failed: {comment_content}"

        # Step 3: Resolve the question
        resolve_content = await call_tool_and_check_content(
            session,
            "resolve_question",
            questionId=question_id,
            resolution="NO",
            questionType="BINARY",
            apiKey=TEST_API_KEY,
        )

        assert resolve_content is not None, "No content in resolve_question response"
        assert resolve_content.lower() == "true", f"Question resolution failed: {resolve_content}"


@pytest.mark.anyio
async def test_create_and_add_forecast_question():
    """Test the full create -> add_forecast -> resolve question flow."""
    from datetime import datetime, timedelta

    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # Verify required tools are available
        required_tools = {"create_question", "add_forecast", "resolve_question"}
        assert required_tools.issubset(available_tools), (
            f"Missing tools: {required_tools - available_tools}"
        )

        # Step 1: Create a test question
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        create_content = await call_tool_and_check_content(
            session,
            "create_question",
            title="MCP Forecast Test Question",
            resolveBy=resolve_date,
            forecast=0.3,
            apiKey=TEST_API_KEY,
            tags=["test", "forecast", "mcp"],
        )

        assert create_content is not None, "No content in create_question response"

        # Parse JSON response to get question ID
        create_data = json.loads(create_content)
        question_id = create_data.get("id")
        title = create_data.get("title")

        assert question_id is not None, "No question ID in response"
        assert title == "MCP Forecast Test Question", f"Unexpected title: {title}"

        # Step 2: Add a forecast to the question
        forecast_content = await call_tool_and_check_content(
            session,
            "add_forecast",
            questionId=question_id,
            forecast=0.8,
            apiKey=TEST_API_KEY,
        )

        assert forecast_content is not None, "No content in add_forecast response"
        assert forecast_content.lower() == "true", f"Adding forecast failed: {forecast_content}"

        # Step 3: Resolve the question
        resolve_content = await call_tool_and_check_content(
            session,
            "resolve_question",
            questionId=question_id,
            resolution="YES",
            questionType="BINARY",
            apiKey=TEST_API_KEY,
        )

        assert resolve_content is not None, "No content in resolve_question response"
        assert resolve_content.lower() == "true", f"Question resolution failed: {resolve_content}"


@pytest.mark.anyio
async def test_structured_get_question():
    """Test that get_question returns a structured Question object."""
    from datetime import datetime, timedelta

    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # Verify required tools are available
        required_tools = {"create_question", "get_question", "delete_question"}
        assert required_tools.issubset(available_tools), (
            f"Missing tools: {required_tools - available_tools}"
        )

        # Step 1: Create a test question
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        create_content = await call_tool_and_check_content(
            session,
            "create_question",
            title="Test Structured Response Question",
            resolveBy=resolve_date,
            forecast=0.75,
            apiKey=TEST_API_KEY,
            tags=["test", "structured", "mcp"],
        )

        assert create_content is not None, "No content in create_question response"

        # Parse JSON response to get question ID
        create_data = json.loads(create_content)
        question_id = create_data.get("id")
        title = create_data.get("title")

        assert question_id is not None, "No question ID in response"
        assert title == "Test Structured Response Question", f"Unexpected title: {title}"

        # Step 2: Test get_question with structured response
        get_content = await call_tool_and_check_content(
            session, "get_question", questionId=question_id, apiKey=TEST_API_KEY
        )

        assert get_content is not None, "No content in get_question response"

        # Step 3: Verify structured JSON response
        question_data = json.loads(get_content)

        # Verify key fields exist (using camelCase as returned by API)
        required_fields = ["id", "title", "type", "resolved", "createdAt", "resolveBy"]
        for field in required_fields:
            assert field in question_data, f"Missing required field: {field}"

        # Verify specific values
        assert question_data["id"] == question_id
        assert question_data["title"] == "Test Structured Response Question"
        assert question_data["type"] == "BINARY"  # Default type
        assert question_data["resolved"] is False  # New question should not be resolved

        # Step 4: Clean up - delete the test question
        delete_content = await call_tool_and_check_content(
            session, "delete_question", questionId=question_id, apiKey=TEST_API_KEY
        )
        assert delete_content.lower() == "true", f"Question deletion failed: {delete_content}"


@pytest.mark.anyio
async def test_create_and_resolve_question():
    """Test the full create -> resolve question flow."""
    from datetime import datetime, timedelta

    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # Verify required tools are available
        required_tools = {"create_question", "resolve_question"}
        assert required_tools.issubset(available_tools), (
            f"Missing tools: {required_tools - available_tools}"
        )

        # Step 1: Create a test question
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        create_content = await call_tool_and_check_content(
            session,
            "create_question",
            title="MCP Integration Test Question",
            resolveBy=resolve_date,
            forecast=0.5,
            apiKey=TEST_API_KEY,
            tags=["test", "mcp"],
        )

        assert create_content is not None, "No content in create_question response"

        # Parse JSON response to get question ID
        create_data = json.loads(create_content)
        question_id = create_data.get("id")
        title = create_data.get("title")

        assert question_id is not None, "No question ID in response"
        assert title == "MCP Integration Test Question", f"Unexpected title: {title}"

        # Step 2: Resolve the question
        resolve_content = await call_tool_and_check_content(
            session,
            "resolve_question",
            questionId=question_id,
            resolution="YES",
            questionType="BINARY",
            apiKey=TEST_API_KEY,
        )

        assert resolve_content is not None, "No content in resolve_question response"
        assert resolve_content.lower() == "true", f"Question resolution failed: {resolve_content}"


@pytest.mark.anyio
async def test_list_resource_templates():
    """Test listing available resource templates."""
    async with create_stdio_mcp_client() as (session, _):
        # Get available resource templates
        templates_response = await session.list_resource_templates()
        available_templates = {
            str(template.uriTemplate) for template in templates_response.resourceTemplates
        }

        # Check for our question resource template
        expected_templates = {"question://{question_id}"}

        for template_uri in expected_templates:
            assert template_uri in available_templates, f"Missing resource template: {template_uri}"

        assert len(available_templates) >= 1, "Should have at least 1 resource template available"


@pytest.mark.anyio
async def test_read_question_resource():
    """Test reading a specific question as a resource."""
    from datetime import datetime, timedelta

    async with create_stdio_mcp_client(include_tools=True) as (
        session,
        available_tools,
    ):
        # First create a test question to read as a resource
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        create_content = await call_tool_and_check_content(
            session,
            "create_question",
            title="Resource Template Test Question",
            resolveBy=resolve_date,
            forecast=0.65,
            apiKey=TEST_API_KEY,
            tags=["resource", "template", "test"],
        )

        assert create_content is not None, "No content in create_question response"

        # Parse JSON response to get question ID
        create_data = json.loads(create_content)
        question_id = create_data.get("id")
        assert question_id is not None, "No question ID in response"

        # Now read the question as a resource using the template
        resource_uri = f"question://{question_id}"
        resource_result = await session.read_resource(resource_uri)

        assert resource_result.contents is not None, "No contents in resource response"
        assert len(resource_result.contents) > 0, "Resource response has no content items"

        # Parse the resource content
        content_item = resource_result.contents[0]
        # Resource content comes as TextResourceContents, not TextContent
        assert hasattr(content_item, "text"), "Resource content should have text attribute"

        question_data = json.loads(content_item.text)

        # Verify it's the same question
        assert question_data["id"] == question_id
        assert question_data["title"] == "Resource Template Test Question"
        assert question_data["type"] == "BINARY"

        # Clean up
        delete_content = await call_tool_and_check_content(
            session, "delete_question", questionId=question_id, apiKey=TEST_API_KEY
        )
        assert delete_content.lower() == "true"
