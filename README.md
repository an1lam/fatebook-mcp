# Fatebook MCP Server

[![CI](https://github.com/an1lam/fatebook-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/an1lam/fatebook-mcp/actions/workflows/ci.yml)

A Model Context Protocol (MCP) server that provides integration with [Fatebook](https://fatebook.io), a prediction tracking platform. This server allows AI assistants like Claude to create, manage, and track predictions directly through MCP.

<a href="https://glama.ai/mcp/servers/@an1lam/fatebook-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@an1lam/fatebook-mcp/badge" alt="Fatebook Server MCP server" />
</a>

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

## Testing and Compatibility

This MCP server has been tested on Mac OS X 14.5 with:

- Claude Code (CLI)
- Claude Desktop
- MCP Inspector

As far as I know, it doesn't violate any MCP protocol requirements but given that MCP is an evolving protocol, certain features or MCP clients may not be fully supported. If you encounter issues with other MCP implementations, please report them as GitHub issues.

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


## Usage with Claude Desktop and [Claude Code](https://www.anthropic.com/claude-code)

### Claude Desktop

Add the following to your Claude Desktop configuration file:

#### macOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Windows
Location: `%APPDATA%\Claude\claude_desktop_config.json`

#### Configuration

```json
{
  "mcpServers": {
    "fatebook": {
      "command": "uv",
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

Replace `/path/to/fatebook-mcp` with the actual path to where you cloned this repository.

### Claude Code (CLI)

For Claude Code, you can add this server in several ways:

#### Option 1: Command line

```bash
# Add the Fatebook MCP server
claude mcp add fatebook --env FATEBOOK_API_KEY=your-api-key-here -- uv run python /path/to/fatebook-mcp/main.py

# Verify it was added successfully
claude mcp list
```

#### Option 2: Import from Claude Desktop

If you already have this configured in Claude Desktop, you can import those settings:

```bash
claude mcp add-from-claude-desktop
```

#### Option 3: Project-specific configuration
Create a `.mcp.json` file in your project:
```json
{
  "mcpServers": {
    "fatebook": {
      "command": "uv",
      "args": ["run", "python", "/path/to/fatebook-mcp/main.py"],
      "env": {
        "FATEBOOK_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Replace `/path/to/fatebook-mcp` with the actual path to where you cloned this repository. As an example, my working configuration looks like:

```json
"fatebook": {
   "command": "/Users/stephenmalina/.local/bin/uv",
   "args": [
"--directory",
     "/Users/stephenmalina/dev/an1lam/fatebook-mcp",
     "run",
     "main.py"
   ],
   "env": {
     "FATEBOOK_API_KEY": "NOTMYREALAPIKEYNICETRY"
   }
}
```



## Development & Testing
### Additional setup
Beyond the above setup that's needed even just to use the MCP server, running the MCP server as standalone and running its tests require fetching your API key and exporting it in your environment.

You can do this either by exporting it directly:

```bash
export FATEBOOK_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```
FATEBOOK_API_KEY=your-api-key-here
```

### Running integration tests

Run the integration tests to verify your setup:

```bash
uv run test_client.py
```

This will test all available endpoints and confirm the server is working correctly.

**Note**: These tests will only succeed if you have the right API key for the test user. If you're developing such that you need to run these tests, for now email me (the author).

### Running the Server Locally

```bash
uv run python main.py
```

The server will start and wait for MCP client connections.

## Testing and Compatibility

This MCP server has been tested with:

- Claude Code (CLI)
- Claude Desktop
- MCP Inspector

As MCP is an evolving protocol, certain features or MCP clients may not be fully supported. If you encounter issues with other MCP implementations, please report them as GitHub issues.

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

## Claude Desktop Examples

**Creating and tracking a prediction:**
![example interaction](./example_claude_desktop_interaction_1.png)

**Reviewing your predictions:**
![example review interaction](./example_claude_desktop_interaction_2.png)


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
