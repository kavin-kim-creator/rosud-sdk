# rosud · Python SDK

> AI agent USDC payment infrastructure — Official Python SDK

```bash
pip install rosud
```

## Quick Start

```python
import rosud

client = rosud.Rosud(api_key="rosud_live_xxx")
# or set ROSUD_API_KEY environment variable

# Create a payment
payment = client.payments.create(
    amount=5.00,
    to="0x742d35Cc6634C0532925a3b8D4C9E3Ff9C4A6bB",
    memo="api_call_fee",
)
print(payment.status)   # "confirmed"
print(payment.tx_hash)  # "0x..."

# Check balance
balance = client.wallets.balance()
print(f"Balance: {balance.usdc} USDC")
```

## Async

```python
import asyncio
import rosud

async def main():
    client = rosud.AsyncRosud(api_key="rosud_live_xxx")
    payment = await client.payments.create(amount=1.00, to="0x...")
    await client.close()

asyncio.run(main())
```

## Resources

- **Payments** — `client.payments.create()`, `.list()`, `.get()`
- **Agents** — `client.agents.create()`, `.list()`, `.get()`, `.delete()`
- **Wallets** — `client.wallets.balance()`
- **Webhooks** — `client.webhooks.create()`, `.list()`, `.delete()`

## Error Handling

```python
from rosud.exceptions import RosudAPIError, RosudAuthError

try:
    payment = client.payments.create(amount=5.00, to="0x...")
except RosudAuthError:
    print("Invalid API key")
except RosudAPIError as e:
    print(e.status_code, e.message)
```

## Links

- [Dashboard](https://rosud.com/dashboard)
- [API Docs](https://rosud.com/docs)
- [TypeScript SDK](https://www.npmjs.com/package/rosud)
- [MCP Server](https://pypi.org/project/rosud-mcp)
