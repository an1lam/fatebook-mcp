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
TEST_API_KEY = os.getenv("FATEBOOK_API_KEY")
if TEST_API_KEY is None:
    raise ValueError("Need FATEBOOK_API_KEY env variable to be set either in .env or the local environment")

# Test user ID for count forecasts testing (from the test API key user)
TEST_USER_ID = "cme6dxa8g0001i7g74q4exorm"


async def test_count_forecasts(session):
    """Test the count_forecasts endpoint."""
    print("🔧 Testing count_forecasts...")
    
    try:
        # Since list_questions now returns formatted text instead of JSON,
        # we'll use the hardcoded test user ID that we know works
        user_id = TEST_USER_ID
        print(f"🔍 Using test user ID: {user_id}")
        
        # Test counting forecasts for the test user ID
        count_result = await session.call_tool("count_forecasts", {
            "userId": user_id
        })
        
        if not count_result.content:
            print("❌ No content in count_forecasts response")
            return False
            
        count_content = count_result.content[0].text
        print(f"📊 Count response: {count_content}")
        
        # Now expecting just an integer response
        try:
            count_value = int(count_content)
            print(f"✅ Found forecast count: {count_value}")
            return True
        except ValueError:
            print(f"❌ Expected integer response, got: {count_content}")
            return False
            
    except Exception as e:
        print(f"❌ Error in count_forecasts test: {e}")
        return False


async def test_create_edit_and_resolve_question(session):
    """Test the full create -> edit -> resolve question flow."""
    print("🔧 Testing create_question -> edit_question -> resolve_question flow...")
    
    # Step 1: Create a test question
    try:
        from datetime import datetime, timedelta
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_result = await session.call_tool("create_question", {
            "title": "MCP Edit Test Question",
            "resolveBy": resolve_date,
            "forecast": 0.7,
            "apiKey": TEST_API_KEY,
            "tags": ["test", "edit", "mcp"]
        })
        
        if not create_result.content:
            print("❌ No content in create_question response")
            return False
            
        create_content = create_result.content[0].text
        print(f"📝 Create response: {create_content}")
        
        # Now expecting a JSON response with id and title
        try:
            create_data = json.loads(create_content)
            question_id = create_data.get('id')
            title = create_data.get('title')
            
            if not question_id:
                print("❌ No question ID in response")
                return False
            
            print(f"✅ Created question with ID: {question_id} and title: {title}")
        except json.JSONDecodeError:
            print(f"❌ Expected JSON response, got: {create_content}")
            return False
        
        # Step 2: Edit the question
        new_resolve_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        edit_result = await session.call_tool("edit_question", {
            "questionId": question_id,
            "title": "MCP Edit Test Question (UPDATED)",
            "resolveBy": new_resolve_date,
            "notes": "This question was updated via MCP integration test",
            "apiKey": TEST_API_KEY
        })
        
        if not edit_result.content:
            print("❌ No content in edit_question response")
            return False
            
        edit_content = edit_result.content[0].text
        print(f"✏️ Edit response: {edit_content}")
        
        # Now expecting a boolean response
        if edit_content.lower() == "true":
            print("✅ Successfully edited question!")
        else:
            print("❌ Question editing failed")
            return False
        
        # Step 3: Resolve the question
        resolve_result = await session.call_tool("resolve_question", {
            "questionId": question_id,
            "resolution": "AMBIGUOUS",
            "questionType": "BINARY",
            "apiKey": TEST_API_KEY
        })
        
        if not resolve_result.content:
            print("❌ No content in resolve_question response")
            return False
            
        resolve_content = resolve_result.content[0].text
        print(f"✅ Resolve response: {resolve_content}")
        
        # Now expecting a boolean response
        if resolve_content.lower() == "true":
            print("✅ Successfully created, edited, and resolved test question!")
            return True
        else:
            print("❌ Question resolution failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in create/edit/resolve flow: {e}")
        return False


async def test_create_and_delete_question(session):
    """Test the full create -> delete question flow."""
    print("🔧 Testing create_question -> delete_question flow...")
    
    # Step 1: Create a test question
    try:
        from datetime import datetime, timedelta
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_result = await session.call_tool("create_question", {
            "title": "MCP Delete Test Question",
            "resolveBy": resolve_date,
            "forecast": 0.6,
            "apiKey": TEST_API_KEY,
            "tags": ["test", "delete", "mcp"]
        })
        
        if not create_result.content:
            print("❌ No content in create_question response")
            return False
            
        create_content = create_result.content[0].text
        print(f"📝 Create response: {create_content}")
        
        # Now expecting a JSON response with id and title
        try:
            create_data = json.loads(create_content)
            question_id = create_data.get('id')
            title = create_data.get('title')
            
            if not question_id:
                print("❌ No question ID in response")
                return False
            
            print(f"✅ Created question with ID: {question_id} and title: {title}")
        except json.JSONDecodeError:
            print(f"❌ Expected JSON response, got: {create_content}")
            return False
        
        # Step 2: Delete the question
        delete_result = await session.call_tool("delete_question", {
            "questionId": question_id,
            "apiKey": TEST_API_KEY
        })
        
        if not delete_result.content:
            print("❌ No content in delete_question response")
            return False
            
        delete_content = delete_result.content[0].text
        print(f"🗑️ Delete response: {delete_content}")
        
        # Now expecting a boolean response
        if delete_content.lower() == "true":
            print("✅ Successfully created and deleted test question!")
            return True
        else:
            print("❌ Question deletion failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in create/delete flow: {e}")
        return False


async def test_create_and_add_comment_question(session):
    """Test the full create -> add_comment -> resolve question flow."""
    print("🔧 Testing create_question -> add_comment -> resolve_question flow...")
    
    # Step 1: Create a test question
    try:
        from datetime import datetime, timedelta
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_result = await session.call_tool("create_question", {
            "title": "MCP Comment Test Question",
            "resolveBy": resolve_date,
            "forecast": 0.4,
            "apiKey": TEST_API_KEY,
            "tags": ["test", "comment", "mcp"]
        })
        
        if not create_result.content:
            print("❌ No content in create_question response")
            return False
            
        create_content = create_result.content[0].text
        print(f"📝 Create response: {create_content}")
        
        # Now expecting a JSON response with id and title
        try:
            create_data = json.loads(create_content)
            question_id = create_data.get('id')
            title = create_data.get('title')
            
            if not question_id:
                print("❌ No question ID in response")
                return False
            
            print(f"✅ Created question with ID: {question_id} and title: {title}")
        except json.JSONDecodeError:
            print(f"❌ Expected JSON response, got: {create_content}")
            return False
        
        # Step 2: Add a comment to the question
        comment_result = await session.call_tool("add_comment", {
            "questionId": question_id,
            "comment": "This is a test comment from the MCP integration test",
            "apiKey": TEST_API_KEY
        })
        
        if not comment_result.content:
            print("❌ No content in add_comment response")
            return False
            
        comment_content = comment_result.content[0].text
        print(f"💬 Comment response: {comment_content}")
        
        # Now expecting a boolean response
        if comment_content.lower() == "true":
            print("✅ Successfully added comment to question!")
        else:
            print("❌ Adding comment failed")
            return False
        
        # Step 3: Resolve the question
        resolve_result = await session.call_tool("resolve_question", {
            "questionId": question_id,
            "resolution": "NO",
            "questionType": "BINARY",
            "apiKey": TEST_API_KEY
        })
        
        if not resolve_result.content:
            print("❌ No content in resolve_question response")
            return False
            
        resolve_content = resolve_result.content[0].text
        print(f"✅ Resolve response: {resolve_content}")
        
        if resolve_content.lower() == "true":
            print("✅ Successfully created, commented, and resolved test question!")
            return True
        else:
            print("❌ Question resolution failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in create/comment/resolve flow: {e}")
        return False


async def test_create_and_add_forecast_question(session):
    """Test the full create -> add_forecast -> resolve question flow."""
    print("🔧 Testing create_question -> add_forecast -> resolve_question flow...")
    
    # Step 1: Create a test question
    try:
        from datetime import datetime, timedelta
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_result = await session.call_tool("create_question", {
            "title": "MCP Forecast Test Question",
            "resolveBy": resolve_date,
            "forecast": 0.3,
            "apiKey": TEST_API_KEY,
            "tags": ["test", "forecast", "mcp"]
        })
        
        if not create_result.content:
            print("❌ No content in create_question response")
            return False
            
        create_content = create_result.content[0].text
        print(f"📝 Create response: {create_content}")
        
        # Now expecting a JSON response with id and title
        try:
            create_data = json.loads(create_content)
            question_id = create_data.get('id')
            title = create_data.get('title')
            
            if not question_id:
                print("❌ No question ID in response")
                return False
            
            print(f"✅ Created question with ID: {question_id} and title: {title}")
        except json.JSONDecodeError:
            print(f"❌ Expected JSON response, got: {create_content}")
            return False
        
        # Step 2: Add a forecast to the question
        forecast_result = await session.call_tool("add_forecast", {
            "questionId": question_id,
            "forecast": 0.8,
            "apiKey": TEST_API_KEY
        })
        
        if not forecast_result.content:
            print("❌ No content in add_forecast response")
            return False
            
        forecast_content = forecast_result.content[0].text
        print(f"📈 Forecast response: {forecast_content}")
        
        # Now expecting a boolean response
        if forecast_content.lower() == "true":
            print("✅ Successfully added forecast to question!")
        else:
            print("❌ Adding forecast failed")
            return False
        
        # Step 3: Resolve the question
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
        
        if resolve_content.lower() == "true":
            print("✅ Successfully created, forecasted, and resolved test question!")
            return True
        else:
            print("❌ Question resolution failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in create/forecast/resolve flow: {e}")
        return False


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
        
        # Now expecting a JSON response with id and title
        try:
            create_data = json.loads(create_content)
            question_id = create_data.get('id')
            title = create_data.get('title')
            
            if not question_id:
                print("❌ No question ID in response")
                return False
            
            print(f"✅ Created question with ID: {question_id} and title: {title}")
        except json.JSONDecodeError:
            print(f"❌ Expected JSON response, got: {create_content}")
            return False
        
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
        
        if resolve_content.lower() == "true":
            print("✅ Successfully created and resolved test question!")
            return True
        else:
            print("❌ Question resolution failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in create/resolve flow: {e}")
        return False


async def test_structured_get_question(session):
    """Test that get_question returns a structured Question object."""
    print("🔧 Testing structured get_question response...")
    
    # First create a question to test with
    try:
        from datetime import datetime, timedelta
        resolve_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_result = await session.call_tool("create_question", {
            "title": "Test Structured Response Question",
            "resolveBy": resolve_date,
            "forecast": 0.75,
            "apiKey": TEST_API_KEY,
            "tags": ["test", "structured", "mcp"]
        })
        
        if not create_result.content:
            print("❌ No content in create_question response")
            return False
            
        create_content = create_result.content[0].text
        
        # Now expecting a JSON response with id and title
        try:
            create_data = json.loads(create_content)
            question_id = create_data.get('id')
            title = create_data.get('title')
            
            if not question_id:
                print("❌ No question ID in response")
                return False
            
            print(f"✅ Created test question with ID: {question_id} and title: {title}")
        except json.JSONDecodeError:
            print(f"❌ Expected JSON response, got: {create_content}")
            return False
        
        # Now test get_question with structured response
        get_result = await session.call_tool("get_question", {
            "questionId": question_id,
            "apiKey": TEST_API_KEY
        })
        
        if not get_result.content:
            print("❌ No content in get_question response")
            return False
        
        # Check if we got a structured response
        content = get_result.content[0]
        
        # MCP always returns TextContent, but for structured responses it's JSON
        if hasattr(content, 'text'):
            try:
                # Try to parse as JSON - if successful, it's structured
                question_data = json.loads(content.text)
                print("✅ Received structured JSON response from get_question")
                
                # Verify key fields exist (using camelCase as returned by API)
                required_fields = ['id', 'title', 'type', 'resolved', 'createdAt', 'resolveBy']
                missing_fields = []
                for field in required_fields:
                    if field not in question_data:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"❌ Missing required fields in structured response: {missing_fields}")
                    return False
                
                print(f"📋 Question ID: {question_data.get('id')}")
                print(f"📋 Title: {question_data.get('title')}")
                print(f"📋 Type: {question_data.get('type')}")
                print(f"📋 Resolved: {question_data.get('resolved')}")
                print(f"📋 Created At: {question_data.get('createdAt')}")
                print(f"📋 Resolve By: {question_data.get('resolveBy')}")
                
                # Check we have nested objects properly formatted
                if 'forecasts' in question_data and question_data['forecasts']:
                    print(f"📋 Forecasts: {len(question_data['forecasts'])} forecast(s)")
                    
                print("✅ Structured response contains all required fields!")
                return True
                
            except json.JSONDecodeError:
                # Not JSON, it's a formatted text response
                print("⚠️ Received formatted text response instead of structured JSON")
                print(f"Response: {content.text[:200]}...")
                return False
        else:
            print(f"❌ Unexpected response format: {type(content)}")
            return False
        
        # Clean up - delete the test question
        await session.call_tool("delete_question", {
            "questionId": question_id,
            "apiKey": TEST_API_KEY
        })
        
        return True
        
    except Exception as e:
        print(f"❌ Error in structured get_question test: {e}")
        import traceback
        traceback.print_exc()
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
            
            # Check the result - now expecting structured JSON response
            list_success = False
            if result.content:
                content = result.content[0].text
                try:
                    # Parse as JSON - expecting QuestionsList format: {"result": [...]}
                    response_data = json.loads(content)
                    
                    if isinstance(response_data, dict) and "result" in response_data:
                        questions_data = response_data["result"]
                        print("✅ Successfully retrieved structured questions list")
                        print(f"✅ Found {len(questions_data)} questions")
                        
                        # Verify structure of first question if any exist
                        if questions_data:
                            first_q = questions_data[0]
                            required_fields = ['id', 'title', 'type', 'resolved', 'createdAt', 'resolveBy']
                            missing_fields = [field for field in required_fields if field not in first_q]
                            
                            if missing_fields:
                                print(f"❌ Missing required fields in first question: {missing_fields}")
                                return False
                            
                            print(f"📋 First question: '{first_q.get('title')}' - {first_q.get('type')} - {'✅ RESOLVED' if first_q.get('resolved') else '⏳ OPEN'}")
                        
                        list_success = True
                    else:
                        print(f"❌ Expected dict with 'result' field, got: {type(response_data)} with keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'N/A'}")
                        return False
                        
                except json.JSONDecodeError:
                    # Fallback: maybe it's still a text response or empty
                    if "No questions found." in content or content.strip() == "[]":
                        print("✅ No questions found (empty list)")
                        list_success = True
                    else:
                        print(f"❌ Could not parse JSON response: {content}")
                        return False
            else:
                print("❌ Error: No content in response")
                return False
            
            # Test create and resolve question flow
            create_resolve_success = await test_create_and_resolve_question(session)
            
            # Test create, add forecast, and resolve question flow
            forecast_success = await test_create_and_add_forecast_question(session)
            
            # Test create, add comment, and resolve question flow
            comment_success = await test_create_and_add_comment_question(session)
            
            # Test create, edit, and resolve question flow
            edit_success = await test_create_edit_and_resolve_question(session)
            
            # Test structured get_question response
            structured_success = await test_structured_get_question(session)
            
            # Test count forecasts
            count_success = await test_count_forecasts(session)
            
            # Test create and delete question flow
            delete_success = await test_create_and_delete_question(session)
            
            return list_success and create_resolve_success and forecast_success and comment_success and edit_success and structured_success and count_success and delete_success
                
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
