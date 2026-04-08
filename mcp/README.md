# Rosud MCP Server

An MCP (Model Context Protocol) server that enables Claude agents to execute **autonomous payments** with USDC stablecoin.

## Available Tools

| Tool | Description |
|------|-------------|
| `create_payment` | Create a payment in USDC |
| `get_balance` | Query current USDC balance |
| `list_payments` | List payment history |
| `get_payment` | Query a specific payment's status |

## Installation

```bash
# Install package
pip install -e "packages/mcp[dev]"

# Or using uv
uv pip install -e "packages/mcp"
```

## Environment Variables

```bash
# Required: Rosud API Key
export ROSUD_API_KEY=rosud_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: API URL (default: http://localhost:8000)
export ROSUD_API_URL=https://api.rosud.io
```

You can obtain an API Key from the Rosud dashboard.

## Adding to Claude Desktop

Add the following to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "rosud": {
      "command": "rosud-mcp",
      "env": {
        "ROSUD_API_KEY": "rosud_live_your_api_key_here",
        "ROSUD_API_URL": "https://api.rosud.io"
      }
    }
  }
}
```

If the `rosud-mcp` command is not in PATH, use the absolute path:

```json
{
  "mcpServers": {
    "rosud": {
      "command": "/path/to/venv/bin/rosud-mcp",
      "env": {
        "ROSUD_API_KEY": "rosud_live_your_api_key_here"
      }
    }
  }
}
```

## Usage Examples

You can make requests like the following in Claude Desktop:

### Check Balance
```
What is my current USDC balance?
```

### Execute Payment
```
Pay the API call fee of $5 to address 0x742d35Cc6634C0532925a3b844Bc454e4438f44e.
Leave memo as 'gpt4_api_call'.
```

### View Payment History
```
Show me the last 10 payment records.
Let me know if there are any failed payments.
```

### Check Payment Status
```
Was payment pay_01HXABCDEF processed?
```

### Complex Workflow
```
Before calling the external data API:
1. Check if the balance is sufficient (minimum 10 USDC required)
2. If the balance is sufficient, pay 9.99 dollars to merchant_data_api
3. Once payment is complete, tell me the payment ID
```

## Running Directly (Development)

```bash
# Run directly in stdio mode
ROSUD_API_KEY=rosud_live_xxx rosud-mcp

# Or run as Python module
ROSUD_API_KEY=rosud_live_xxx python -m rosud_mcp.server
```

## Running Tests

```bash
cd packages/mcp
pip install -e ".[dev]"
pytest tests/ -v
```

## Architecture

```
Claude Desktop
     │ MCP Protocol (stdio)
     ▼
rosud_mcp.server   ← MCP Server (app)
     │ tool call
     ▼
rosud_mcp.tools    ← Tool definitions + handlers
     │ HTTP request
     ▼
rosud_mcp.client   ← httpx AsyncClient
     │ X-API-Key auth
     ▼
Rosud Payment API  ← FastAPI (apps/api)
     │
     ▼
Circle USDC API    ← Base L2 blockchain
```

## Security Notes

- Do not hardcode the API Key in code. Always use environment variables.
- Payments are irreversible. Always verify the amount and recipient address.
- Using `idempotency_key` allows safe retries on network errors.
