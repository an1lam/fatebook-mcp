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
