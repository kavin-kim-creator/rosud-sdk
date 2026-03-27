# rosud · TypeScript SDK

> AI agent USDC payment infrastructure — Official TypeScript/JavaScript SDK

[![npm version](https://badge.fury.io/js/rosud.svg)](https://badge.fury.io/js/rosud)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18-brightgreen)](https://nodejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)](https://www.typescriptlang.org/)

## Installation

```bash
npm install rosud
# or
pnpm add rosud
# or
yarn add rosud
```

> **Requires Node.js 18+** (native `fetch` support)

## Quick Start

```typescript
import Rosud from 'rosud'

const client = new Rosud({ apiKey: 'rosud_live_xxx' })
// Or use environment variable: ROSUD_API_KEY=rosud_live_xxx

// Check your USDC balance
const { usdc } = await client.wallets.balance()
console.log(`Balance: ${usdc} USDC`)

// Send a payment
const payment = await client.payments.create({
  amount: 5.00,
  to: '0x742d35Cc6634C0532925a3b8D4C9E3Ff9C4A6bB',
  memo: 'api_call_fee',
})
console.log(`Payment ${payment.id} — status: ${payment.status}`)
```

## Usage

### Initialization

```typescript
import Rosud from 'rosud'

// Option 1: pass apiKey directly
const client = new Rosud({ apiKey: 'rosud_live_xxx' })

// Option 2: use environment variable (recommended for production)
// export ROSUD_API_KEY=rosud_live_xxx
const client = new Rosud()

// Option 3: custom base URL (for testing or self-hosted)
const client = new Rosud({
  apiKey: process.env.ROSUD_API_KEY,
  baseUrl: 'https://api.staging.rosud.com',
  timeoutMs: 10_000, // 10 seconds (default: 30s)
})
```

### Payments

```typescript
// Create a payment
const payment = await client.payments.create({
  amount: 1.50,           // USDC amount
  to: '0xRecipient...',   // destination wallet address
  memo: 'service_fee',    // optional label
  idempotency_key: 'order-abc-001', // safe to retry with same key
})

// List payments with filters
const { items, total } = await client.payments.list({
  status: 'confirmed',
  limit: 20,
  offset: 0,
  agent_id: 'agent-uuid', // filter by agent (optional)
})

// Get a single payment by ID
const payment = await client.payments.get('pay_abc123')

console.log(payment.tx_hash)    // on-chain transaction hash
console.log(payment.confirmed_at) // settlement timestamp
```

**Payment statuses:** `pending` → `processing` → `confirmed` | `failed`

### Agents

Register sub-agents with spending limits so they can make payments autonomously:

```typescript
// Create an agent with daily and per-transaction limits
const agent = await client.agents.create({
  name: 'research-agent-v1',
  spending_limit_daily: 1000,    // max $1000 USDC/day
  spending_limit_per_tx: 50,     // max $50 USDC per payment
  allowed_recipients: [          // whitelist (optional)
    '0xAllowedAddr1...',
    '0xAllowedAddr2...',
  ],
})

// ⚠️  agent.api_key is only returned on creation — save it securely!
console.log('Agent API Key:', agent.api_key)

// List all agents
const agents = await client.agents.list()

// Get a specific agent
const agent = await client.agents.get(agentId)

// Deactivate / delete an agent
await client.agents.delete(agentId)
```

### Wallets

```typescript
// Get your USDC balance
const { usdc, wallet_id, network } = await client.wallets.balance()
console.log(`${usdc} USDC on ${network}`)  // e.g. "42.50 USDC on base"
```

### Webhooks

Get real-time notifications when payments are confirmed or fail:

```typescript
// Register a webhook endpoint
const webhook = await client.webhooks.create({
  url: 'https://your-server.com/webhooks/rosud',
  events: ['payment.confirmed', 'payment.failed'],
  secret: 'your-signing-secret', // used for HMAC verification
})

// List registered webhooks
const hooks = await client.webhooks.list()

// Remove a webhook
await client.webhooks.delete(webhookId)
```

#### Webhook Payload Verification

```typescript
import crypto from 'crypto'

function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex')
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  )
}

// In your Express/Fastify handler:
app.post('/webhooks/rosud', express.raw({ type: '*/*' }), (req, res) => {
  const sig = req.headers['x-rosud-signature'] as string
  const valid = verifyWebhookSignature(req.body.toString(), sig, process.env.WEBHOOK_SECRET!)
  if (!valid) return res.status(401).send('Invalid signature')

  const event = JSON.parse(req.body.toString())
  console.log('Payment confirmed:', event.data.id)
  res.sendStatus(200)
})
```

## x402 Facilitator

Rosud implements the [x402 protocol](https://github.com/coinbase/x402) as a Facilitator on Base.

### Verify Payment

```typescript
const response = await fetch("https://api.rosud.com/v1/x402/verify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    x402Version: 2,
    accepted: {
      scheme: "exact",
      network: "eip155:8453",
      amount: "1000000",
      asset: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      payTo: "0xYOUR_WALLET",
      maxTimeoutSeconds: 60,
      extra: {}
    },
    payload: {
      signature: "0x...",
      authorization: {
        from: "0xPAYER",
        to: "0xYOUR_WALLET",
        value: "1000000",
        validAfter: "0",
        validBefore: "9999999999",
        nonce: "0x" + "0".repeat(64)
      }
    }
  })
})
const { isValid, invalidReason } = await response.json()
```

### Settle Payment

```typescript
const response = await fetch("https://api.rosud.com/v1/x402/settle", {
  method: "POST",
  headers: {
    "Authorization": "Bearer rsd_YOUR_API_KEY",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ ... }) // same structure as verify
})
const { success, txHash, network } = await response.json()
```

## Error Handling

```typescript
import Rosud, { RosudError } from 'rosud'

try {
  await client.payments.create({ amount: 999999, to: '0x...' })
} catch (e) {
  if (e instanceof RosudError) {
    console.error(`[${e.status}] ${e.code}: ${e.message}`)
    // Examples:
    //   [402] insufficient_balance: Not enough USDC balance
    //   [429] rate_limit_exceeded: Too many requests
    //   [400] invalid_address: Recipient address is not a valid EVM address
  } else {
    throw e // re-throw unexpected errors
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|---|---|---|
| `missing_api_key` | 401 | API key not provided |
| `invalid_api_key` | 401 | API key is invalid or revoked |
| `insufficient_balance` | 402 | Not enough USDC to complete payment |
| `spending_limit_exceeded` | 403 | Agent spending limit reached |
| `invalid_address` | 400 | Recipient wallet address is invalid |
| `rate_limit_exceeded` | 429 | Too many requests — back off and retry |
| `payment_not_found` | 404 | Payment ID does not exist |

## TypeScript Types

All types are exported for use in your application:

```typescript
import type {
  Payment,
  PaymentStatus,
  Agent,
  Webhook,
  WalletBalance,
  CreatePaymentParams,
  CreateAgentParams,
  CreateWebhookParams,
  RosudClientOptions,
} from 'rosud'
```

## Environment Variables

| Variable | Description |
|---|---|
| `ROSUD_API_KEY` | Your Rosud API key (`rosud_live_xxx`) — required |

## Examples

Real-world usage patterns:

```typescript
// Pattern 1: Agent autonomously pays for API calls
const agentClient = new Rosud({ apiKey: process.env.AGENT_API_KEY })

async function callExternalAPI(endpoint: string) {
  // Pay for the API call first
  await agentClient.payments.create({
    amount: 0.01,
    to: '0xAPIProviderWallet...',
    memo: `api:${endpoint}`,
    idempotency_key: `${endpoint}-${Date.now()}`,
  })
  // Then call the API
  return fetch(endpoint)
}

// Pattern 2: Monitor agent spending
const operatorClient = new Rosud({ apiKey: process.env.OPERATOR_API_KEY })

async function getDailySpend(agentId: string): Promise<number> {
  const { items } = await operatorClient.payments.list({
    agent_id: agentId,
    status: 'confirmed',
    limit: 100,
  })
  return items.reduce((sum, p) => sum + parseFloat(p.amount), 0)
}

// Pattern 3: Batch payment with idempotency
async function payMultiple(recipients: { address: string; amount: number; id: string }[]) {
  return Promise.allSettled(
    recipients.map(r =>
      client.payments.create({
        to: r.address,
        amount: r.amount,
        idempotency_key: `batch-${r.id}`,
      })
    )
  )
}
```

---

## npm Publishing Guide

This section documents how to publish new versions of the SDK to npm.

### Prerequisites

1. **npm account** with publish access to the `rosud` package
2. **Build tools** installed: `npm install` in this directory
3. Logged in: `npm login` (or use an automation token)

### Publishing Steps

```bash
# 1. Install dependencies
cd sdk-ts
npm install

# 2. Bump version (choose one)
npm version patch   # 0.1.0 → 0.1.1  (bug fixes)
npm version minor   # 0.1.0 → 0.2.0  (new features, backward compatible)
npm version major   # 0.1.0 → 1.0.0  (breaking changes)

# 3. Build the package
npm run build
# Output: dist/index.js (CJS), dist/index.mjs (ESM), dist/index.d.ts (types)

# 4. Verify the build
ls dist/
node -e "const r = require('./dist/index.js'); console.log(typeof r.default)"

# 5. Preview what will be published
npm pack --dry-run

# 6. Publish to npm
npm publish
# For first-time publish: npm publish --access public
```

### Versioning Policy

| Change Type | Version Bump | Examples |
|---|---|---|
| Bug fix, docs | `patch` | Fix typo, fix type error |
| New API method | `minor` | Add new resource, new option |
| Breaking change | `major` | Rename method, remove param |

### Automated Publishing (CI/CD)

For GitHub Actions automated publishing on tag push:

```yaml
# .github/workflows/publish-ts-sdk.yml
name: Publish TypeScript SDK

on:
  push:
    tags:
      - 'sdk-ts/v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: sdk-ts
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci
      - run: npm run build
      - run: npm run typecheck
      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**To trigger a release:**
```bash
git tag sdk-ts/v0.2.0
git push origin sdk-ts/v0.2.0
```

### Pre-release Versions

For beta/alpha releases before a stable version:

```bash
# Publish as beta (won't be installed by default)
npm version prerelease --preid=beta   # → 0.2.0-beta.0
npm publish --tag beta

# Users install beta explicitly:
npm install rosud@beta
```

### Post-publish Checklist

- [ ] Verify on [npmjs.com/package/rosud](https://npmjs.com/package/rosud)
- [ ] Test install: `npm install rosud@latest` in a fresh directory
- [ ] Tag the Git commit: `git tag sdk-ts/v<version> && git push --tags`
- [ ] Update [CHANGELOG.md](./CHANGELOG.md) with release notes
- [ ] Announce in team Slack/Telegram

---

## Development

```bash
# Install dependencies
npm install

# Build (CJS + ESM + types)
npm run build

# Watch mode for development
npm run dev

# Type check without building
npm run typecheck
```

### Project Structure

```
sdk-ts/
├── src/
│   └── index.ts      # All SDK source (types, HTTP client, resources)
├── dist/             # Built output (git-ignored)
│   ├── index.js      # CommonJS
│   ├── index.mjs     # ES Module
│   └── index.d.ts    # TypeScript declarations
├── package.json
└── README.md
```

## Links

- 🌐 [rosud.com](https://rosud.com)
- 📚 [API Docs](https://rosud.com/docs)
- 🐍 [Python SDK](../sdk/)
- 🔌 [MCP Server](../mcp/)
- 📦 [npm package](https://www.npmjs.com/package/rosud)
- 🐛 [Issues](https://github.com/kavin-kim-creator/rosud/issues)
