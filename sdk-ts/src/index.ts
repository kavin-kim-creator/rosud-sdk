// ─── Types ────────────────────────────────────────────────────────────────────

export type PaymentStatus = 'pending' | 'processing' | 'confirmed' | 'failed'
export type Currency = 'USDC'

export interface Payment {
  id: string
  agent_id: string | null
  operator_id: string
  amount: string
  currency: Currency
  network: string
  from_wallet: string | null
  to_wallet: string
  memo: string | null
  status: PaymentStatus
  fee: string | null
  tx_hash: string | null
  idempotency_key: string | null
  created_at: string
  confirmed_at: string | null
}

export interface PaymentListResponse {
  items: Payment[]
  total: number
  limit: number
  offset: number
}

export interface Agent {
  id: string
  operator_id: string
  name: string
  spending_limit_daily: string | null
  spending_limit_per_tx: string | null
  allowed_recipients: string[] | null
  is_active: boolean
  created_at: string
  api_key?: string // only on creation
}

export interface Webhook {
  id: string
  operator_id: string
  url: string
  events: string[]
  is_active: boolean
  created_at: string
}

export interface WalletBalance {
  wallet_id: string
  usdc: string
  network: string
}

// ─── Request types ─────────────────────────────────────────────────────────────

export interface CreatePaymentParams {
  amount: number | string
  to: string
  memo?: string
  currency?: Currency
  idempotency_key?: string
  agent_id?: string
}

export interface ListPaymentsParams {
  limit?: number
  offset?: number
  status?: PaymentStatus
  agent_id?: string
}

export interface CreateAgentParams {
  name: string
  spending_limit_daily?: number | null
  spending_limit_per_tx?: number | null
  allowed_recipients?: string[] | null
}

export interface CreateWebhookParams {
  url: string
  events: string[]
  secret?: string
}

// ─── Error ─────────────────────────────────────────────────────────────────────

export class RosudError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'RosudError'
    this.status = status
    this.code = code
  }
}

// ─── HTTP client ───────────────────────────────────────────────────────────────

const DEFAULT_BASE_URL = 'https://api.rosud.com'
const DEFAULT_TIMEOUT_MS = 30_000
const SDK_VERSION = '0.1.0'

interface RequestOptions {
  method?: string
  body?: unknown
  params?: Record<string, string | number | undefined>
}

class RosudHTTP {
  private readonly apiKey: string
  private readonly baseUrl: string
  private readonly timeoutMs: number

  constructor(apiKey: string, baseUrl: string, timeoutMs: number) {
    this.apiKey = apiKey
    this.baseUrl = baseUrl.replace(/\/$/, '')
    this.timeoutMs = timeoutMs
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, params } = options

    let url = `${this.baseUrl}${endpoint}`
    if (params) {
      const qs = Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join('&')
      if (qs) url += `?${qs}`
    }

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.timeoutMs)

    try {
      const res = await fetch(url, {
        method,
        headers: {
          'X-API-Key': this.apiKey,
          'Content-Type': 'application/json',
          'User-Agent': `rosud-ts/${SDK_VERSION}`,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      if (res.status === 204) return undefined as T

      const data = await res.json().catch(() => ({}))

      if (!res.ok) {
        const detail = data?.detail
        const code = typeof detail === 'object' ? (detail?.error ?? 'api_error') : 'api_error'
        const msg = typeof detail === 'object' ? (detail?.message ?? res.statusText) : (detail ?? res.statusText)
        throw new RosudError(res.status, code, msg)
      }

      return data as T
    } finally {
      clearTimeout(timer)
    }
  }
}

// ─── Resources ─────────────────────────────────────────────────────────────────

class PaymentsResource {
  constructor(private readonly http: RosudHTTP) {}

  /** Create a payment */
  create(params: CreatePaymentParams): Promise<Payment> {
    return this.http.request<Payment>('/v1/payments', { method: 'POST', body: params })
  }

  /** List payments */
  list(params?: ListPaymentsParams): Promise<PaymentListResponse> {
    return this.http.request<PaymentListResponse>('/v1/payments', {
      params: params as Record<string, string | number | undefined>,
    })
  }

  /** Get a single payment */
  get(paymentId: string): Promise<Payment> {
    return this.http.request<Payment>(`/v1/payments/${paymentId}`)
  }
}

class AgentsResource {
  constructor(private readonly http: RosudHTTP) {}

  /** List agents */
  list(): Promise<Agent[]> {
    return this.http.request<Agent[]>('/v1/agents')
  }

  /** Create an agent */
  create(params: CreateAgentParams): Promise<Agent> {
    return this.http.request<Agent>('/v1/agents', { method: 'POST', body: params })
  }

  /** Get an agent */
  get(agentId: string): Promise<Agent> {
    return this.http.request<Agent>(`/v1/agents/${agentId}`)
  }

  /** Delete an agent */
  delete(agentId: string): Promise<void> {
    return this.http.request<void>(`/v1/agents/${agentId}`, { method: 'DELETE' })
  }
}

class WalletsResource {
  constructor(private readonly http: RosudHTTP) {}

  /** Query USDC balance */
  balance(): Promise<WalletBalance> {
    return this.http.request<WalletBalance>('/v1/wallets/balance')
  }
}

class WebhooksResource {
  constructor(private readonly http: RosudHTTP) {}

  /** List webhooks */
  list(): Promise<Webhook[]> {
    return this.http.request<Webhook[]>('/v1/webhooks')
  }

  /** Create a webhook */
  create(params: CreateWebhookParams): Promise<Webhook> {
    return this.http.request<Webhook>('/v1/webhooks', { method: 'POST', body: params })
  }

  /** Delete a webhook */
  delete(webhookId: string): Promise<void> {
    return this.http.request<void>(`/v1/webhooks/${webhookId}`, { method: 'DELETE' })
  }
}

// ─── Main Client ───────────────────────────────────────────────────────────────

export interface RosudClientOptions {
  /** Rosud API key (rosud_live_xxx). Falls back to ROSUD_API_KEY env var if not provided */
  apiKey?: string
  /** API server URL (default: https://api.rosud.com) */
  baseUrl?: string
  /** Request timeout in ms (default: 30000) */
  timeoutMs?: number
}

export class Rosud {
  readonly payments: PaymentsResource
  readonly agents: AgentsResource
  readonly wallets: WalletsResource
  readonly webhooks: WebhooksResource

  constructor(options: RosudClientOptions = {}) {
    const apiKey =
      options.apiKey ??
      (typeof process !== 'undefined' ? process.env.ROSUD_API_KEY : undefined)

    if (!apiKey) {
      throw new RosudError(
        0,
        'missing_api_key',
        'API key is required. Use new Rosud({ apiKey: "rosud_live_xxx" }) or set the ROSUD_API_KEY environment variable.'
      )
    }

    const http = new RosudHTTP(
      apiKey,
      options.baseUrl ?? DEFAULT_BASE_URL,
      options.timeoutMs ?? DEFAULT_TIMEOUT_MS
    )

    this.payments = new PaymentsResource(http)
    this.agents = new AgentsResource(http)
    this.wallets = new WalletsResource(http)
    this.webhooks = new WebhooksResource(http)
  }
}

/** Default export (convenience) */
export default Rosud
