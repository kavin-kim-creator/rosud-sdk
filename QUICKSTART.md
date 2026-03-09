# 🚀 Rosud — Design Partner Quickstart

> **지금 바로 에이전트에 결제를 심어보세요.**
> AI 에이전트가 직접 USDC 결제를 처리합니다 — 사람 개입 없이.

---

## Step 1 — API 키 발급

1. [rosud.com/dashboard](https://rosud.com/dashboard) 접속
2. 회원가입 → **API Keys** 메뉴
3. **"Create API Key"** 클릭 → `rosud_live_xxx` 형태의 키 발급

```bash
export ROSUD_API_KEY="rosud_live_xxx"
```

---

## Step 2 — 에이전트 등록

에이전트에 USDC 지갑을 연결합니다.

```python
import rosud

client = rosud.Rosud(api_key="rosud_live_xxx")

# 에이전트 등록
agent = client.agents.create(
    name="my-gpt-agent",
    wallet="0xYourWalletAddress",   # USDC 받을 지갑 주소
)

print(agent.id)   # agt_01HXYZ...
print(agent.wallet)
```

**지갑 주소가 없다면?**
- MetaMask 설치 → Base Network 추가 → 주소 복사
- 또는 [Coinbase Wallet](https://wallet.coinbase.com/) 사용

---

## Step 3 — 첫 결제 실행

에이전트가 자율적으로 결제를 생성합니다.

```python
# 에이전트가 외부 API에 결제
payment = client.payments.create(
    amount=1.00,                                  # USDC
    to="0xRecipientWalletAddress",
    memo="data_api_call_fee",
)

print(payment.status)    # "confirmed"
print(payment.tx_hash)   # Base L2 트랜잭션 해시
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

## Step 4 — 잔액 확인

```python
balance = client.wallets.balance()
print(f"USDC 잔액: {balance.usdc}")
```

---

## Step 5 — Webhook 설정 (선택)

결제 완료 알림을 받으려면:

```python
webhook = client.webhooks.create(
    url="https://yourapp.com/webhook",
    events=["payment.confirmed", "payment.failed"],
)
```

---

## Claude MCP 연동

Claude가 직접 결제를 실행하게 하려면:

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

Claude에서 바로 사용:
> "0x742d...에 5 USDC 보내줘"

---

## 문제가 생기면

- 📖 [API 문서](https://rosud.com/docs)
- 💬 카빈님께 직접 연락 (Design Partner 전용 지원)
- 🐛 [GitHub Issues](https://github.com/kavin-kim-creator/rosud-sdk/issues)

---

*Design Partner 여러분의 피드백이 Rosud를 만들어갑니다. 솔직한 의견 부탁드립니다!*
