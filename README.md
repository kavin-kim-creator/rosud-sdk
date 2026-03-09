# Rosud SDK

> **The payment layer for AI agents.** Send and receive USDC with one line of code.

[![PyPI](https://img.shields.io/pypi/v/rosud?color=blue)](https://pypi.org/project/rosud/)
[![npm](https://img.shields.io/npm/v/rosud?color=blue)](https://www.npmjs.com/package/rosud)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![rosud.com](https://img.shields.io/badge/site-rosud.com-black)](https://rosud.com)

AI agents can now pay for APIs, delegate tasks, and settle invoices — autonomously, in USDC.

🌐 [rosud.com](https://rosud.com) · 📖 [Docs](https://rosud.com/docs) · 🚀 [Get API Key](https://rosud.com/dashboard)

---

## ⚡ 5-Minute Quickstart

### Python
```bash
pip install rosud
```

```python
import rosud

client = rosud.Rosud(api_key="rosud_live_xxx")

# Your AI agent sends a payment
payment = client.payments.create(
    amount=5.00,
    to="0x742d35Cc6634C0532925a3b8D4C9E3Ff9C4A6bB",
    memo="api_call_fee",
)
print(payment.status)   # "confirmed"
print(payment.tx_hash)  # "0xabc..."
```

### TypeScript
```bash
npm install rosud
```

```typescript
import Rosud from 'rosud';

const client = new Rosud({ apiKey: 'rosud_live_xxx' });

const payment = await client.payments.create({
  amount: 5.00,
  to: '0x742d35Cc6634C0532925a3b8D4C9E3Ff9C4A6bB',
  memo: 'api_call_fee',
});
```

### Claude MCP Server
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
Claude can now call `create_payment`, `get_balance`, `list_payments` directly.

---

## 📦 Packages

| Package | Description | Install |
|---------|-------------|---------|
| [`sdk/`](./sdk) | Python SDK | `pip install rosud` |
| [`sdk-ts/`](./sdk-ts) | TypeScript SDK | `npm install rosud` |
| [`mcp/`](./mcp) | MCP Server for Claude | `pip install rosud-mcp` |

---

## 🤖 Why Rosud?

AI agents are making decisions — but they can't pay for anything.

Rosud gives your agent a USDC wallet and a simple API:
- **Register** an agent with a wallet address
- **Create payments** with a single API call
- **Receive webhooks** when payments confirm
- **Works with** LangChain, AutoGen, Claude, GPT — any agent framework

```python
# LangChain agent that can pay for external APIs
from langchain.tools import tool
import rosud

client = rosud.Rosud(api_key="rosud_live_xxx")

@tool
def pay_for_data(amount: float, wallet: str) -> str:
    """Pay an external data provider in USDC"""
    payment = client.payments.create(amount=amount, to=wallet)
    return f"Payment {payment.id} sent: {payment.status}"
```

---

## 🔗 Links

- [Dashboard](https://rosud.com/dashboard) — Get your API key
- [API Reference](https://rosud.com/docs) — Full endpoint docs
- [PyPI](https://pypi.org/project/rosud/) — Python package
- [npm](https://www.npmjs.com/package/rosud) — TypeScript package

---

## License

MIT © [Sandinzone](https://rosud.com)
