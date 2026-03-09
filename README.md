# Rosud SDK

> AI agent stablecoin payment infrastructure — Official SDKs and MCP Server

[![PyPI](https://img.shields.io/pypi/v/rosud)](https://pypi.org/project/rosud/)
[![npm](https://img.shields.io/npm/v/rosud)](https://www.npmjs.com/package/rosud)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Rosud** lets AI agents autonomously send and receive USDC payments via a simple API.

🌐 [rosud.com](https://rosud.com) · 📖 [Docs](https://rosud.com/docs) · 🚀 [Get API Key](https://rosud.com/dashboard)

---

## Packages

| Package | Description | Install |
|---------|-------------|---------|
| [`sdk/`](./sdk) | Python SDK | `pip install rosud` |
| [`sdk-ts/`](./sdk-ts) | TypeScript SDK | `npm install rosud` |
| [`mcp/`](./mcp) | MCP Server for Claude | `pip install rosud-mcp` |

---

## Quick Start (Python)

```python
import rosud

client = rosud.Rosud(api_key="rosud_live_xxx")

# Create a payment
payment = client.payments.create(
    amount=5.00,
    to="0x742d35Cc6634C0532925a3b8D4C9E3Ff9C4A6bB",
    currency="USDC"
)
print(payment.id)
```

## Quick Start (TypeScript)

```typescript
import Rosud from 'rosud';

const client = new Rosud({ apiKey: 'rosud_live_xxx' });

const payment = await client.payments.create({
  amount: 5.00,
  to: '0x742d35Cc6634C0532925a3b8D4C9E3Ff9C4A6bB',
  currency: 'USDC',
});
```

## MCP Server (Claude)

```json
{
  "mcpServers": {
    "rosud": {
      "command": "python",
      "args": ["-m", "rosud_mcp"],
      "env": { "ROSUD_API_KEY": "rosud_live_xxx" }
    }
  }
}
```

---

## License

MIT © [Sandinzone](https://rosud.com)
