#!/usr/bin/env python3
"""
Simple integration test client for the Fatebook MCP server.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test API key for integration testing
TEST_API_KEY = "s9dsge0vjrbndoqr9xyq"


async def test_create_and_resolve_question(session):
    """Test the full create -> resolve question flow."""
    print("🔧 Testing create_question -> resolve_question flow...")
    
    # Step 1: Create a test question
    try:
        from datetime import datetime, timedelta
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_result = await session.call_tool("create_question", {
            "title": "MCP Integration Test Question",
            "resolveBy": resolve_date,
            "forecast": 0.5,
            "apiKey": TEST_API_KEY,
            "tags": ["test", "mcp"]
        })
        
        if not create_result.content:
            print("❌ No content in create_question response")
            return False
            
        create_content = create_result.content[0].text
        print(f"📝 Create response: {create_content}")
        
        if "successfully" not in create_content:
            print("❌ Question creation failed")
            return False
            
        # Extract question ID from response URL
        # Response format: "Question created successfully: https://fatebook.io/q/title--QUESTION_ID"
        if "https://fatebook.io/q/" not in create_content:
            print("❌ Could not find Fatebook URL in create response")
            return False
            
        # Extract question ID from the URL
        url_start = create_content.find("https://fatebook.io/q/")
        url = create_content[url_start:].strip()
        # Question ID is after the last double dash
        if "--" not in url:
            print("❌ Could not parse question ID from URL format")
            return False
            
        question_id = url.split("--")[-1]
        
        if not question_id:
            print("❌ Could not extract question ID from URL")
            return False
            
        print(f"✅ Created question with ID: {question_id}")
        
        # Step 2: Resolve the question
        resolve_result = await session.call_tool("resolve_question", {
            "questionId": question_id,
            "resolution": "YES",
            "questionType": "BINARY",
            "apiKey": TEST_API_KEY
        })
        
        if not resolve_result.content:
            print("❌ No content in resolve_question response")
            return False
            
        resolve_content = resolve_result.content[0].text
        print(f"✅ Resolve response: {resolve_content}")
        
        if "successfully" in resolve_content:
            print("✅ Successfully created and resolved test question!")
            return True
        else:
            print("❌ Question resolution failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in create/resolve flow: {e}")
        return False


async def test_fatebook_server():
    """Test the Fatebook MCP server by calling list_questions tool."""
    
    print(f"✅ Using test API key: {TEST_API_KEY[:10]}...")
    
    async with AsyncExitStack() as stack:
        # Start the server
        server_params = StdioServerParameters(
            command="uv", 
            args=["run", "python", "main.py"],
            env=None
        )
        
        try:
            # Connect to server
            stdio_transport = await stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await stack.enter_async_context(ClientSession(read, write))
            
            print("✅ Connected to Fatebook MCP server")
            
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools_response = await session.list_tools()
            print(f"✅ Available tools: {[tool.name for tool in tools_response.tools]}")
            
            # Test list_questions tool
            if "list_questions" not in [tool.name for tool in tools_response.tools]:
                print("❌ Error: list_questions tool not found")
                return False
            
            # Call the list_questions tool with a limit using test API key
            print("📡 Calling list_questions tool...")
            result = await session.call_tool("list_questions", {
                "limit": 3, 
                "apiKey": TEST_API_KEY
            })
            
            # Check the result
            list_success = False
            if result.content:
                content = result.content[0].text
                if "Questions data:" in content:
                    print("✅ Successfully retrieved questions data")
                    # Try to parse the JSON to validate structure
                    try:
                        json_start = content.find("{")
                        if json_start != -1:
                            json_data = content[json_start:]
                            parsed = json.loads(json_data)
                            if "items" in parsed:
                                print(f"✅ Found {len(parsed['items'])} questions")
                                list_success = True
                            else:
                                print("❌ Error: No 'items' field in response")
                                return False
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parsing JSON: {e}")
                        return False
                else:
                    print(f"❌ Unexpected response: {content}")
                    return False
            else:
                print("❌ Error: No content in response")
                return False
            
            # Test create and resolve question flow
            create_resolve_success = await test_create_and_resolve_question(session)
            
            return list_success and create_resolve_success
                
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            return False


async def main():
    """Main test function."""
    print("🚀 Starting Fatebook MCP server integration test...")
    
    success = await test_fatebook_server()
    
    if success:
        print("✅ All tests passed! Fatebook MCP server is working correctly.")
        sys.exit(0)
    else:
        print("❌ Tests failed! Check the server implementation.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())