"""
기본 결제 예시 - Rosud Python SDK

이 예시는 Rosud SDK의 기본 사용법을 보여줍니다:
- 결제 생성
- 결제 목록 조회
- 지갑 잔액 조회
- 에이전트 생성
"""
import os

import rosud
from rosud.exceptions import InsufficientFundsError, PaymentError, RosudError


def main() -> None:
    # API 키 설정 (환경변수 또는 직접 전달)
    client = rosud.Rosud(
        api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_your_key_here"),
        base_url=os.environ.get("ROSUD_BASE_URL", "https://api.rosud.com"),
    )

    # ──────────────────────────────────────────────
    # 1. 지갑 잔액 확인
    # ──────────────────────────────────────────────
    print("=== 지갑 잔액 ===")
    try:
        balance = client.wallets.get_balance()
        print(f"잔액: {balance.amount} {balance.currency}")
        print(f"주소: {balance.address}")
        print(f"네트워크: {balance.network}")
    except RosudError as e:
        print(f"잔액 조회 실패: {e.message}")

    # ──────────────────────────────────────────────
    # 2. 결제 생성
    # ──────────────────────────────────────────────
    print("\n=== 결제 생성 ===")
    try:
        payment = client.payments.create(
            amount=5.00,
            currency="USDC",
            to="0xRecipientWalletAddress123456789012345678",
            memo="api_call_fee",
            idempotency_key="unique-payment-key-001",  # 중복 방지
        )
        print(f"결제 ID: {payment.id}")
        print(f"상태: {payment.status}")
        print(f"금액: {payment.amount} {payment.currency}")
        print(f"수신자: {payment.to_wallet}")
        print(f"TX Hash: {payment.tx_hash or '(pending)'}")
    except InsufficientFundsError:
        print("잔액이 부족합니다.")
    except PaymentError as e:
        print(f"결제 오류 [{e.error_code}]: {e.message}")
    except RosudError as e:
        print(f"오류: {e.message}")

    # ──────────────────────────────────────────────
    # 3. 결제 목록 조회
    # ──────────────────────────────────────────────
    print("\n=== 최근 결제 목록 ===")
    try:
        payments = client.payments.list(limit=10)
        print(f"총 {payments.total}건 중 {len(payments)}건 조회")
        for p in payments:
            print(f"  - {p.id} | {p.amount} USDC | {p.status} | {p.created_at:%Y-%m-%d %H:%M}")
    except RosudError as e:
        print(f"결제 목록 조회 실패: {e.message}")

    # ──────────────────────────────────────────────
    # 4. 에이전트 생성 (AI 에이전트용 서브계정)
    # ──────────────────────────────────────────────
    print("\n=== 에이전트 생성 ===")
    try:
        agent = client.agents.create(
            name="Payment Bot v1",
            spending_limit_daily=100.00,      # 일 100 USDC 한도
            spending_limit_per_tx=10.00,       # 건당 10 USDC 한도
            allowed_recipients=[               # 화이트리스트 (보안)
                "0xApprovedRecipient1",
                "0xApprovedRecipient2",
            ],
        )
        print(f"에이전트 ID: {agent.id}")
        print(f"에이전트 이름: {agent.name}")
        print(f"API 키: {agent.api_key}")  # 최초 1회만 반환!
        print("⚠️  API 키를 안전하게 보관하세요. 다시 조회할 수 없습니다.")
    except RosudError as e:
        print(f"에이전트 생성 실패: {e.message}")

    # ──────────────────────────────────────────────
    # 5. context manager 사용법
    # ──────────────────────────────────────────────
    print("\n=== Context Manager 사용 ===")
    with rosud.Rosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_key")) as c:
        try:
            balance = c.wallets.get_balance()
            print(f"잔액: {balance.amount} USDC")
        except RosudError as e:
            print(f"오류: {e}")

    client.close()
    print("\n완료!")


if __name__ == "__main__":
    main()
