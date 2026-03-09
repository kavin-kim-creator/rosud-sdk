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

  /** 결제 생성 */
  create(params: CreatePaymentParams): Promise<Payment> {
    return this.http.request<Payment>('/v1/payments', { method: 'POST', body: params })
  }

  /** 결제 목록 조회 */
  list(params?: ListPaymentsParams): Promise<PaymentListResponse> {
    return this.http.request<PaymentListResponse>('/v1/payments', {
      params: params as Record<string, string | number | undefined>,
    })
  }

  /** 단일 결제 조회 */
  get(paymentId: string): Promise<Payment> {
    return this.http.request<Payment>(`/v1/payments/${paymentId}`)
  }
}

class AgentsResource {
  constructor(private readonly http: RosudHTTP) {}

  /** 에이전트 목록 조회 */
  list(): Promise<Agent[]> {
    return this.http.request<Agent[]>('/v1/agents')
  }

  /** 에이전트 생성 */
  create(params: CreateAgentParams): Promise<Agent> {
    return this.http.request<Agent>('/v1/agents', { method: 'POST', body: params })
  }

  /** 에이전트 조회 */
  get(agentId: string): Promise<Agent> {
    return this.http.request<Agent>(`/v1/agents/${agentId}`)
  }

  /** 에이전트 삭제 */
  delete(agentId: string): Promise<void> {
    return this.http.request<void>(`/v1/agents/${agentId}`, { method: 'DELETE' })
  }
}

class WalletsResource {
  constructor(private readonly http: RosudHTTP) {}

  /** USDC 잔액 조회 */
  balance(): Promise<WalletBalance> {
    return this.http.request<WalletBalance>('/v1/wallets/balance')
  }
}

class WebhooksResource {
  constructor(private readonly http: RosudHTTP) {}

  /** Webhook 목록 조회 */
  list(): Promise<Webhook[]> {
    return this.http.request<Webhook[]>('/v1/webhooks')
  }

  /** Webhook 생성 */
  create(params: CreateWebhookParams): Promise<Webhook> {
    return this.http.request<Webhook>('/v1/webhooks', { method: 'POST', body: params })
  }

  /** Webhook 삭제 */
  delete(webhookId: string): Promise<void> {
    return this.http.request<void>(`/v1/webhooks/${webhookId}`, { method: 'DELETE' })
  }
}

// ─── Main Client ───────────────────────────────────────────────────────────────

export interface RosudClientOptions {
  /** Rosud API 키 (rosud_live_xxx). 미제공 시 ROSUD_API_KEY 환경변수 사용 */
  apiKey?: string
  /** API 서버 URL (기본값: https://api.rosud.com) */
  baseUrl?: string
  /** 요청 타임아웃 ms (기본값: 30000) */
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
        'API 키가 필요합니다. new Rosud({ apiKey: "rosud_live_xxx" }) 또는 ROSUD_API_KEY 환경변수를 설정하세요.'
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

/** 기본 export (편의용) */
export default Rosud
