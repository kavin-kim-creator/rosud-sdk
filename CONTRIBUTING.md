# Contributing to Rosud SDK

Thanks for your interest in contributing! This guide covers how to contribute to the Python SDK, TypeScript SDK, and MCP server.

## Table of Contents

- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Python SDK (`sdk/`)](#python-sdk-sdk)
- [TypeScript SDK (`sdk-ts/`)](#typescript-sdk-sdk-ts)
- [MCP Server (`mcp/`)](#mcp-server-mcp)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Project Structure

```
rosud-sdk/
├── sdk/          # Python SDK (pip install rosud)
│   ├── rosud/    # Source code
│   ├── tests/    # Pytest tests
│   └── pyproject.toml
├── sdk-ts/       # TypeScript SDK (npm install rosud)
│   ├── src/      # Source code
│   └── package.json
├── mcp/          # MCP Server for Claude
└── README.md
```

---

## Development Setup

### Clone & configure

```bash
git clone https://github.com/sandinzone/rosud-sdk.git
cd rosud-sdk
```

Get a test API key from [rosud.com/dashboard](https://rosud.com/dashboard) and set it as an environment variable:

```bash
export ROSUD_API_KEY="rosud_test_xxx"
```

> **Note:** Use a `rosud_test_` key (not `rosud_live_`) for development. Test keys hit the sandbox environment and do not move real funds.

---

## Python SDK (`sdk/`)

### Setup

```bash
cd sdk
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run tests

```bash
# All tests
pytest

# Single file
pytest tests/test_client.py

# With coverage
pytest --cov=rosud --cov-report=term-missing
```

### Code style

We use `ruff` for linting and formatting:

```bash
ruff check rosud/
ruff format rosud/
```

### Adding a new resource (e.g. `invoices`)

1. Create `rosud/resources/invoices.py`:

```python
from ..models import Invoice
from .._http import HttpClient


class InvoicesResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(self, *, amount: float, to: str, memo: str = "") -> Invoice:
        data = self._http.post("/v1/invoices", json={"amount": amount, "to": to, "memo": memo})
        return Invoice(**data)

    def get(self, invoice_id: str) -> Invoice:
        data = self._http.get(f"/v1/invoices/{invoice_id}")
        return Invoice(**data)
```

2. Register it in `rosud/client.py`:

```python
from .resources.invoices import InvoicesResource

class Rosud:
    def __init__(self, ...):
        ...
        self.invoices = InvoicesResource(self._http)
```

3. Add the `Invoice` model to `rosud/models.py`.

4. Write tests in `tests/test_invoices.py`.

### Adding a new exception

Add it to `rosud/exceptions.py` and raise it in `rosud/_http.py` based on the HTTP status code.

---

## TypeScript SDK (`sdk-ts/`)

### Setup

```bash
cd sdk-ts
npm install
```

### Run tests

```bash
npm test
```

### Type-check

```bash
npm run typecheck
```

### Build

```bash
npm run build
# Output: dist/index.cjs, dist/index.mjs, dist/index.d.ts
```

### Adding a new resource (e.g. `invoices`)

1. Create `src/resources/invoices.ts`:

```typescript
import type { HttpClient } from '../http';

export interface Invoice {
  id: string;
  amount: number;
  to: string;
  memo: string;
  status: 'pending' | 'confirmed' | 'failed';
  createdAt: string;
}

export interface CreateInvoiceParams {
  amount: number;
  to: string;
  memo?: string;
}

export class InvoicesResource {
  constructor(private readonly http: HttpClient) {}

  async create(params: CreateInvoiceParams): Promise<Invoice> {
    return this.http.post<Invoice>('/v1/invoices', params);
  }

  async get(invoiceId: string): Promise<Invoice> {
    return this.http.get<Invoice>(`/v1/invoices/${invoiceId}`);
  }
}
```

2. Export from `src/index.ts` and wire it up in the main `Rosud` class.

3. Add tests in `src/__tests__/invoices.test.ts`.

### Style

- Strict TypeScript (`"strict": true` in tsconfig)
- No `any` — use `unknown` + type guards instead
- Async methods return `Promise<T>`, not callbacks

---

## MCP Server (`mcp/`)

The MCP server exposes Rosud tools to Claude and other MCP-compatible agents.

### Setup

```bash
cd mcp
pip install -e ".[dev]"
```

### Adding a new tool

1. Define the tool in `rosud_mcp/tools.py`:

```python
@mcp.tool()
async def create_invoice(amount: float, to: str, memo: str = "") -> dict:
    """Create a payment invoice for an agent to fulfill."""
    invoice = client.invoices.create(amount=amount, to=to, memo=memo)
    return invoice.model_dump()
```

2. Update `mcp/README.md` with the new tool name and description.

---

## Commit Guidelines

All commits must be in **English**. Use these prefixes:

| Prefix | Purpose |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `refactor:` | Code refactoring |
| `docs:` | Documentation changes |
| `test:` | Test additions or fixes |
| `chore:` | Config, deps, or miscellaneous |

Use optional scopes to clarify which package is affected:

```
feat(sdk): add invoices resource
fix(sdk-ts): handle 429 rate limit errors
docs(mcp): add Claude Desktop config example
test(sdk): add webhook signature validation tests
```

### Examples

```
feat(sdk): add AsyncRosud support for invoices
fix(sdk-ts): correct TypeScript types for payment status enum
docs: add CONTRIBUTING guide with SDK development instructions
chore(sdk): bump httpx to 0.27.0
```

---

## Pull Request Process

1. **Fork** the repo and create a feature branch: `git checkout -b feat/invoice-resource`
2. **Write tests** — PRs without tests for new features will not be merged
3. **Run the full test suite** before pushing (`pytest` / `npm test`)
4. **Update docs** — if you add a public method, update the relevant `README.md`
5. **Open a PR** with a clear title and description of what changed and why
6. **One topic per PR** — don't bundle unrelated changes

### PR checklist

- [ ] Tests pass locally
- [ ] No linting errors (`ruff check` / `npm run typecheck`)
- [ ] Relevant docs updated
- [ ] Commit messages follow the guidelines above

---

## Need Help?

- Open a [GitHub Issue](https://github.com/sandinzone/rosud-sdk/issues) for bugs or feature requests
- Check [rosud.com/docs](https://rosud.com/docs) for API reference
- Reach out at [team@rosud.com](mailto:team@rosud.com) for anything else

---

MIT © [Sandinzone](https://rosud.com)
