# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Fatebook MCP (Model Context Protocol) server implementation in Python. The project uses MCP to provide integration with Fatebook.

## Development Setup

This project uses `uv` for Python dependency management. Ensure Python 3.13+ is available.

### Key Commands

```bash
# Install dependencies
uv sync

# Run the main script
uv run python main.py

# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>
```

## Project Structure

- `main.py` - Entry point for the MCP server
- `pyproject.toml` - Python project configuration and dependencies
- `uv.lock` - Locked dependency versions

## Dependencies

- `httpx` - HTTP client library for making API requests
- `mcp[cli]` - Model Context Protocol implementation with CLI support

## Fatebook API Integration

Base URL: `https://fatebook.io/api/v0/`

### API Endpoints

1. **Get Questions**: `GET /getQuestions`
   - Required: `apiKey`
   - Optional: `resolved`, `unresolved`, `searchString`, `limit`, `cursor`
   - Fetch personal or public questions with filtering

2. **Create Question**: `POST /createQuestion`
   - Required: `apiKey`, `title`, `resolveBy`, `forecast` (0-1)
   - Optional: `tags`, `sharePublicly`, `shareWithLists`, `shareWithEmail`, `hideForecastsUntil`

3. **Get Question**: `GET /getQuestion`
   - Required: `apiKey`, `questionId`

4. **Resolve Question**: `POST /resolveQuestion`
   - Required: `questionId`, `resolution` (YES/NO/AMBIGUOUS), `questionType`, `apiKey`
   - Supports binary and multi-choice questions

5. **Add Forecast**: `POST /addForecast`
   - Required: `questionId`, `forecast` (0-1), `apiKey`
   - Optional: `optionId` for multi-choice questions

6. **Add Comment**: `POST /addComment`
   - Required: `questionId`, `comment`, `apiKey`

7. **Edit Question**: `PATCH /editQuestion`
   - Optional updates: `title`, `resolveBy`, `notes`

8. **Delete Question**: `DELETE /deleteQuestion`
   - Required: `questionId`, `apiKey`

9. **Set Visibility**: `PATCH /setSharedPublicly`
   - Parameters: `questionId`, `sharedPublicly` (boolean), `unlisted` (boolean)

10. **Count Forecasts**: `GET /countForecasts`
    - Required: `userId`

### Authentication

- API key authentication required for most endpoints
- API key obtained from https://fatebook.io/api-setup

### Important Notes

- Forecast values must be between 0 and 1
- Use ISO 8601 format for datetime fields
- OpenAPI spec available at https://fatebook.io/api/openapi.json