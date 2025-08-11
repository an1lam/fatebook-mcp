# Fatebook MCP Server

A Model Context Protocol (MCP) server that provides integration with [Fatebook](https://fatebook.io), a prediction tracking platform. This server allows AI assistants like Claude to create, manage, and track predictions directly through MCP.

## Features

- **Create Questions**: Make predictions with forecasts (0-100% probability)
- **List Questions**: View your predictions with filtering options
- **Get Question Details**: Retrieve comprehensive information about specific questions
- **Add Forecasts**: Update your predicted probabilities on existing questions
- **Add Comments**: Add commentary to track your reasoning
- **Resolve Questions**: Mark questions as resolved (YES/NO/AMBIGUOUS)
- **Edit Questions**: Update question titles, resolve dates, and notes
- **Delete Questions**: Remove questions you no longer need
- **Count Forecasts**: Track your forecasting activity

## Installation

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- A Fatebook account and API key

### Getting your Fatebook API Key

1. Sign in to [Fatebook](https://fatebook.io)
2. Navigate to [API Setup](https://fatebook.io/api-setup)
3. Generate and copy your API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fatebook-mcp.git
cd fatebook-mcp
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up your API key (optional - you can also provide it per request):
```bash
export FATEBOOK_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
FATEBOOK_API_KEY=your-api-key-here
```

## Usage with Claude Desktop

Add the following to your Claude Desktop configuration file:

### macOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Location: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration

```json
{
  "mcpServers": {
    "fatebook": {
      "command": "path/to/uv",
      "args": [
        "run",
        "python",
        "/path/to/fatebook-mcp/main.py"
      ],
      "env": {
        "FATEBOOK_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Replace `/path/to/fatebook-mcp` with the actual path to where you cloned this repository and path/to/uv with the output of `which uv`.

## Development & Testing

### Running integration tests
Run the integration tests to verify your setup:

```bash
uv run test_client.py
```

This will test all available endpoints and confirm the server is working correctly.

### Running the Server Locally

```bash
uv run python main.py
```

The server will start and wait for MCP client connections.

## Troubleshooting

### API Key Issues
- Ensure your API key is valid and active
- Check that the API key is properly set in environment or config
- Try providing the API key directly in the request

### Connection Issues
- Verify the server path in your Claude Desktop config is correct
- Check that Python 3.13+ is installed and accessible
- Ensure uv dependencies are properly installed with `uv sync`

### Question Format
- Dates should be in YYYY-MM-DD format
- Forecast values must be between 0.0 and 1.0
- Question IDs are provided when creating questions

## Example Conversations with Claude

**Creating and tracking a prediction:**
```
User: Create a Fatebook question about whether it will rain tomorrow in SF, resolving tomorrow, 70% chance

Claude: I'll create that Fatebook question for you.

**Question Created Successfully!**
Title: Will it rain tomorrow in SF?
ID: cme6h2si00001bwlzf9qg7tt0
URL: https://fatebook.io/q/will-it-rain-tomorrow-in-sf--cme6h2si00001bwlzf9qg7tt0

User: Actually, checking the weather forecast, update my prediction to 40%

Claude: I'll update your forecast to 40% for that question.

Forecast added successfully!
```

**Reviewing your predictions:**
```
User: Show me my unresolved Fatebook questions about AI

Claude: Here are your unresolved questions about AI:

**Will GPT-5 be released by end of 2025?**
? OPEN | ID: cme6h2si00001bwlzf9qg7tt0 | 3 forecasts | Tags: ai, openai

**Will any AI system score >90% on ARC-AGI by 2025?**
? OPEN | ID: cme1m5hde0007142kojke80mp | 5 forecasts | Tags: ai, benchmarks
```

## API Documentation

For more details about the Fatebook API, see:
- [Fatebook API Setup](https://fatebook.io/api-setup)
- [OpenAPI Specification](https://fatebook.io/api/openapi.json)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For issues with:
- **This MCP server**: Open an issue on GitHub
- **Fatebook API**: Contact Fatebook support
- **MCP/Claude Desktop**: See [MCP documentation](https://modelcontextprotocol.io)
