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


async def test_fatebook_server():
    """Test the Fatebook MCP server by calling list_questions tool."""
    
    # Verify API key is available
    api_key = os.getenv("FATEBOOK_API_KEY")
    if not api_key:
        print("❌ Error: FATEBOOK_API_KEY not found in environment")
        return False
    
    print(f"✅ Found API key: {api_key[:10]}...")
    
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
            
            # Call the list_questions tool with a limit
            print("📡 Calling list_questions tool...")
            result = await session.call_tool("list_questions", {"limit": 3})
            
            # Check the result
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
                                return True
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