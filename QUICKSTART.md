# 🚀 Rosud — Design Partner Quickstart

> **Embed payments into your agent right now.**
> AI agents handle USDC payments directly — no human intervention.

---

## Step 1 — Get an API Key

1. Go to [rosud.com/dashboard](https://rosud.com/dashboard)
2. Sign up → **API Keys** menu
3. Click **"Create API Key"** → get a key in the format `rosud_live_xxx`

```bash
export ROSUD_API_KEY="rosud_live_xxx"
```

---

## Step 2 — Register an Agent

Connect a USDC wallet to your agent.

```python
import rosud

client = rosud.Rosud(api_key="rosud_live_xxx")

# Register an agent
agent = client.agents.create(
    name="my-gpt-agent",
    wallet="0xYourWalletAddress",   # Wallet address to receive USDC
)

print(agent.id)   # agt_01HXYZ...
print(agent.wallet)
```

**Don't have a wallet address?**
- Install MetaMask → Add Base Network → Copy address
- Or use [Coinbase Wallet](https://wallet.coinbase.com/)

---

## Step 3 — Run Your First Payment

Your agent autonomously creates a payment.

```python
# Agent pays an external API
payment = client.payments.create(
    amount=1.00,                                  # USDC
    to="0xRecipientWalletAddress",
    memo="data_api_call_fee",
)

print(payment.status)    # "confirmed"
print(payment.tx_hash)   # Base L2 transaction hash
```

**TypeScript:**
```typescript
import Rosud from 'rosud';
const client = new Rosud({ apiKey: 'rosud_live_xxx' });

const payment = await client.payments.create({
  amount: 1.00,
  to: '0xRecipientWalletAddress',
  memo: 'data_api_call_fee',
});
```

---

## Step 4 — Check Balance

```python
balance = client.wallets.balance()
print(f"USDC Balance: {balance.usdc}")
```

---

## Step 5 — Set Up Webhooks (Optional)

To receive payment completion notifications:

```python
webhook = client.webhooks.create(
    url="https://yourapp.com/webhook",
    events=["payment.confirmed", "payment.failed"],
)
```

---

## Claude MCP Integration

To let Claude execute payments directly:

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "rosud": {
      "command": "python",
      "args": ["-m", "rosud_mcp"],
      "env": {
        "ROSUD_API_KEY": "rosud_live_xxx"
      }
    }
  }
}
```

Use directly in Claude:
> "Send 5 USDC to 0x742d..."

---

## Troubleshooting

- 📖 [API Docs](https://rosud.com/docs)
- 💬 Contact Kavin directly (Design Partner dedicated support)
- 🐛 [GitHub Issues](https://github.com/kavin-kim-creator/rosud-sdk/issues)

---

*Your feedback as a Design Partner shapes Rosud. Please be honest!*
