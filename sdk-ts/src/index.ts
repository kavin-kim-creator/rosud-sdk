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

// ─── Webhook Verification ─────────────────────────────────────────────────────

/**
 * Verifies a Rosud webhook signature.
 *
 * The server includes an `X-Rosud-Signature: sha256=<hex>` header in every webhook request.
 * Use this function to confirm that the request was genuinely sent from the Rosud server.
 *
 * @example
 * ```typescript
 * // Next.js App Router
 * export async function POST(req: Request) {
 *   const body = await req.text()
 *   const isValid = await verifyWebhook(
 *     body,
 *     req.headers.get('x-rosud-signature')!,
 *     process.env.ROSUD_WEBHOOK_SECRET!
 *   )
 *   if (!isValid) return Response.json({ error: 'Invalid signature' }, { status: 401 })
 * }
 * ```
 */
export async function verifyWebhook(
  payload: string,
  signature: string,
  secret: string,
): Promise<boolean> {
  if (!signature || !secret) return false
  const parts = signature.split('=')
  if (parts.length !== 2 || parts[0] !== 'sha256') return false
  const expectedHex = parts[1]
  try {
    const encoder = new TextEncoder()
    const key = await crypto.subtle.importKey('raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
    const sig = await crypto.subtle.sign('HMAC', key, encoder.encode(payload))
    const computed = Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('')
    if (computed.length !== expectedHex.length) return false
    let diff = 0
    for (let i = 0; i < computed.length; i++) diff |= computed.charCodeAt(i) ^ expectedHex.charCodeAt(i)
    return diff === 0
  } catch { return false }
}

/** Node.js-only synchronous webhook verification */
export function verifyWebhookSync(payload: string, signature: string, secret: string): boolean {
  if (!signature || !secret) return false
  const parts = signature.split('=')
  if (parts.length !== 2 || parts[0] !== 'sha256') return false
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const nc = typeof require !== 'undefined' ? (() => { try { return require('crypto') } catch { return null } })() : null
  if (!nc) throw new Error('verifyWebhookSync is Node.js only. Use verifyWebhook (async) in browsers.')
  const computed = nc.createHmac('sha256', secret).update(payload).digest('hex')
  if (computed.length !== parts[1].length) return false
  return nc.timingSafeEqual(Buffer.from(computed, 'hex'), Buffer.from(parts[1], 'hex'))
}

// ─── x402 Protocol Support ────────────────────────────────────────────────────

export interface X402Options {
  /** Maximum USDC to spend per request (default: 0.10) */
  maxPrice?: number
  /** Optional Rosud agent ID for spending limit tracking */
  agentId?: string
  /** Optional payment memo */
  memo?: string
  /** Additional HTTP headers */
  headers?: Record<string, string>
  /** Request body (for POST/PUT) */
  body?: unknown
}

export interface X402Response {
  /** HTTP status code of the final response */
  status: number
  /** Whether a payment was made */
  paid: boolean
  /** Rosud payment ID (if paid) */
  paymentId?: string
  /** Amount paid in USDC (if paid) */
  amountUsdc?: number
  /** Response body text */
  body: string
  /** Parsed JSON body (if Content-Type is application/json) */
  json?: unknown
}

/**
 * Fetch an x402-protected URL, automatically paying via Rosud if a 402 is returned.
 *
 * The x402 protocol enables per-request HTTP micropayments.
 * This function handles the full payment flow using Rosud as the payment facilitator.
 *
 * @example
 * ```typescript
 * import Rosud, { payAndFetch } from 'rosud'
 *
 * const client = new Rosud({ apiKey: 'rosud_live_xxx' })
 *
 * const result = await payAndFetch('https://api.example.com/premium', client, {
 *   maxPrice: 0.05,
 *   agentId: 'agent_abc',
 * })
 * console.log(result.paid, result.body)
 * ```
 */
export async function payAndFetch(
  url: string,
  rosudClient: Rosud,
  options: X402Options & { method?: string } = {},
): Promise<X402Response> {
  const { method = 'GET', maxPrice = 0.10, agentId, memo, headers = {}, body } = options
  const reqInit: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json', ...headers },
    ...(body ? { body: JSON.stringify(body) } : {}),
  }

  // Step 1: Initial request — check if payment is needed
  const initial = await fetch(url, reqInit)
  if (initial.status !== 402) {
    const text = await initial.text()
    return { status: initial.status, paid: false, body: text.slice(0, 2000), json: tryParseJson(text) }
  }

  // Step 2: Parse PAYMENT-REQUIRED header (x402 protocol)
  const prHeader = initial.headers.get('PAYMENT-REQUIRED') ?? initial.headers.get('payment-required')
  if (!prHeader) throw new Error('402 received but no PAYMENT-REQUIRED header found.')

  let paymentRequired: unknown
  try { paymentRequired = JSON.parse(atob(prHeader)) }
  catch { throw new Error(`Failed to decode PAYMENT-REQUIRED header: ${prHeader.slice(0, 100)}`) }

  const pr = paymentRequired as Record<string, unknown>
  const accepts = (pr['accepts'] as unknown[]) ?? []
  if (!accepts.length) throw new Error('No payment requirements in 402 response.')

  // Step 3: Select cheapest requirement within budget
  let selected: unknown = null
  for (const req of accepts) {
    const r = req as Record<string, unknown>
    const raw = parseFloat(String(r['maxAmountRequired'] ?? r['amount'] ?? '0'))
    const priceUsdc = raw > 1000 ? raw / 1_000_000 : raw
    if (priceUsdc <= maxPrice) { selected = req; break }
  }
  if (!selected) throw new Error(`All payment requirements exceed maxPrice=${maxPrice} USDC.`)

  // Step 4: Ask Rosud to pay on behalf of the agent
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const payResult = await (rosudClient as any)._http.request<{
    payment_signature?: string; payment_id?: string; amount_usdc?: number; error?: string
  }>('/x402/pay', {
    method: 'POST',
    body: { url, method, payment_requirement: selected, payment_required: paymentRequired, agent_id: agentId, memo: memo ?? `x402:${url}` },
  })

  if (payResult.error) throw new Error(`Rosud payment failed: ${payResult.error}`)
  if (!payResult.payment_signature) throw new Error('Rosud did not return payment_signature.')

  // Step 5: Retry with payment signature
  const final = await fetch(url, {
    ...reqInit,
    headers: { ...(reqInit.headers as Record<string, string>), ...headers, 'PAYMENT-SIGNATURE': payResult.payment_signature },
  })
  const finalText = await final.text()
  return { status: final.status, paid: true, paymentId: payResult.payment_id, amountUsdc: payResult.amount_usdc, body: finalText.slice(0, 2000), json: tryParseJson(finalText) }
}

function tryParseJson(text: string): unknown {
  try { return JSON.parse(text) } catch { return undefined }
}

/**
 * Reusable x402 client backed by Rosud — pay-per-request APIs made simple.
 *
 * @example
 * ```typescript
 * import Rosud, { X402Client } from 'rosud'
 *
 * const rosud = new Rosud({ apiKey: 'rosud_live_xxx' })
 * const x402 = new X402Client(rosud, { maxPrice: 0.05, agentId: 'my-agent' })
 *
 * const weather = await x402.get('https://api.example.com/weather')
 * const result  = await x402.post('https://api.example.com/infer', { prompt: 'hello' })
 * console.log(weather.paid, weather.json)
 * ```
 */
export class X402Client {
  constructor(
    private readonly rosud: Rosud,
    private readonly defaults: X402Options = {},
  ) {}

  async request(method: string, url: string, body?: unknown, opts: X402Options = {}): Promise<X402Response> {
    return payAndFetch(url, this.rosud, { ...this.defaults, ...opts, method, body: body ?? opts.body })
  }

  get(url: string, opts?: X402Options)                { return this.request('GET',    url, undefined, opts) }
  post(url: string, body?: unknown, opts?: X402Options) { return this.request('POST',   url, body,      opts) }
  put(url: string,  body?: unknown, opts?: X402Options) { return this.request('PUT',    url, body,      opts) }
  delete(url: string, opts?: X402Options)              { return this.request('DELETE', url, undefined, opts) }
}
