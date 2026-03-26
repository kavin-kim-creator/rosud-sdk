# Changelog — rosud TypeScript SDK

All notable changes to this package will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

## [0.1.0] — 2026-03-XX

### Added
- Initial release of the Rosud TypeScript/JavaScript SDK
- `client.payments.create()` — send USDC payments
- `client.payments.list()` — list payments with filters (status, agent_id, pagination)
- `client.payments.get(id)` — fetch single payment by ID
- `client.agents.create()` — register sub-agents with spending limits
- `client.agents.list()` — list all agents
- `client.agents.get(id)` — fetch single agent
- `client.agents.delete(id)` — deactivate/remove an agent
- `client.wallets.balance()` — get USDC balance
- `client.webhooks.create()` — register webhook endpoint
- `client.webhooks.list()` — list webhooks
- `client.webhooks.delete(id)` — remove webhook
- `RosudError` class with `status`, `code`, and `message` fields
- Full TypeScript types exported for all request/response types
- ESM + CJS dual build via tsup
- Node.js 18+ support (native fetch)
- `ROSUD_API_KEY` environment variable support

---

[Unreleased]: https://github.com/kavin-kim-creator/rosud/compare/sdk-ts/v0.1.0...HEAD
[0.1.0]: https://github.com/kavin-kim-creator/rosud/releases/tag/sdk-ts/v0.1.0
