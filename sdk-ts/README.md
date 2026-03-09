# rosud · TypeScript SDK

> AI agent USDC payment infrastructure — Official TypeScript/JavaScript SDK

```bash
npm install rosud
# or
pnpm add rosud
```

## Quick Start

```typescript
import Rosud from 'rosud'

const client = new Rosud({ apiKey: 'rosud_live_xxx' })
// or set ROSUD_API_KEY environment variable

// Create a payment
const payment = await client.payments.create({
  amount: 5.00,
  to: '0x742d35Cc6634C0532925a3b8D4C9E3Ff9C4A6bB',
  memo: 'api_call_fee',
})
console.log(payment.id, payment.status)

// Check balance
const { usdc } = await client.wallets.balance()
console.log(`Balance: ${usdc} USDC`)

// List recent payments
const { items } = await client.payments.list({ limit: 10, status: 'confirmed' })
```

## Usage

### Payments

```typescript
// Create payment
const payment = await client.payments.create({
  amount: 1.50,
  to: '0xRecipient...',
  memo: 'service_fee',
  idempotency_key: 'unique-key-001', // safe to retry
})

// List payments
const { items, total } = await client.payments.list({
  status: 'confirmed',
  limit: 20,
  offset: 0,
})

// Get single payment
const p = await client.payments.get('payment-id')
```

### Agents

```typescript
// Create agent with spending limits
const agent = await client.agents.create({
  name: 'trading-bot-1',
  spending_limit_daily: 1000,   // max $1000/day
  spending_limit_per_tx: 100,   // max $100/tx
})
// agent.api_key is returned only on creation — save it!

// List agents
const agents = await client.agents.list()

// Delete agent
await client.agents.delete(agentId)
```

### Webhooks

```typescript
// Register webhook
const webhook = await client.webhooks.create({
  url: 'https://your-server.com/webhooks/rosud',
  events: ['payment.confirmed', 'payment.failed'],
  secret: 'your-hmac-secret',
})

// List webhooks
const hooks = await client.webhooks.list()

// Delete webhook
await client.webhooks.delete(webhookId)
```

## Error Handling

```typescript
import Rosud, { RosudError } from 'rosud'

try {
  await client.payments.create({ amount: 5, to: '0x...' })
} catch (e) {
  if (e instanceof RosudError) {
    console.error(e.status, e.code, e.message)
    // e.g.: 400 'insufficient_balance' 'Not enough USDC balance'
  }
}
```

## Environment Variables

| Variable | Description |
|---|---|
| `ROSUD_API_KEY` | Your Rosud API key (required if not passed to constructor) |

## Links

- [Dashboard](https://rosud.com/dashboard)
- [API Docs](https://rosud.com/docs)
- [Python SDK](../sdk/)
- [MCP Server](../mcp/)
