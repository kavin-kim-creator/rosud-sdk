"""
웹훅 설정 & 처리 예시 - Rosud Python SDK

Rosud 웹훅을 사용하면 결제 이벤트(confirmed, failed, pending 등)를
실시간으로 서버에서 수신할 수 있습니다.

이 예시에서 다루는 내용:
- 웹훅 등록 / 조회 / 삭제
- HMAC 서명 검증 (보안 필수!)
- FastAPI로 웹훅 수신 서버 구현
- 이벤트 타입별 처리 패턴
"""
import hashlib
import hmac
import json
import os
import time
from typing import Any

import rosud
from rosud.exceptions import RosudError

# ──────────────────────────────────────────────────────────
# 1. 웹훅 등록
# ──────────────────────────────────────────────────────────

def setup_webhook() -> None:
    """웹훅 엔드포인트를 Rosud에 등록하는 예시"""
    client = rosud.Rosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx"))

    # 웹훅 시크릿은 안전하게 보관해야 합니다 (HMAC 서명 검증에 사용)
    WEBHOOK_SECRET = os.environ.get("ROSUD_WEBHOOK_SECRET", "my-super-secret-key")

    try:
        # 웹훅 등록
        webhook = client.webhooks.create(
            url="https://myapp.com/webhooks/rosud",
            events=[
                "payment.confirmed",   # 결제 완료
                "payment.failed",      # 결제 실패
                "payment.pending",     # 결제 대기 중
            ],
            secret=WEBHOOK_SECRET,
        )
        print(f"✅ 웹훅 등록 완료")
        print(f"   ID: {webhook.id}")
        print(f"   URL: {webhook.url}")
        print(f"   이벤트: {', '.join(webhook.events)}")
        print(f"   활성화: {webhook.is_active}")

    except RosudError as e:
        print(f"❌ 웹훅 등록 실패: {e.message}")

    client.close()


def list_and_manage_webhooks() -> None:
    """웹훅 목록 조회 및 관리 예시"""
    client = rosud.Rosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx"))

    try:
        # 전체 웹훅 목록 조회
        webhooks = client.webhooks.list()
        print(f"📋 등록된 웹훅: {webhooks.total}개\n")

        for wh in webhooks:
            status = "✅" if wh.is_active else "⏸"
            print(f"  {status} {wh.id}")
            print(f"     URL: {wh.url}")
            print(f"     이벤트: {', '.join(wh.events)}")
            print(f"     등록일: {wh.created_at:%Y-%m-%d %H:%M}")
            print()

        # 특정 웹훅 삭제 (예시)
        if webhooks.total > 0:
            wh_id = webhooks.items[0].id
            client.webhooks.delete(str(wh_id))
            print(f"🗑️  웹훅 {wh_id} 삭제 완료")

    except RosudError as e:
        print(f"오류: {e.message}")

    client.close()


# ──────────────────────────────────────────────────────────
# 2. HMAC 서명 검증 유틸리티
# ──────────────────────────────────────────────────────────

def verify_webhook_signature(
    payload_body: bytes,
    signature_header: str,
    secret: str,
    max_age_seconds: int = 300,  # 5분 이내 요청만 허용 (replay attack 방어)
) -> bool:
    """
    Rosud 웹훅 서명을 검증합니다.

    서명 형식: "t=타임스탬프,v1=HMAC-SHA256-HEX"
    예: "t=1711234567,v1=abc123def456..."

    Args:
        payload_body: 요청 바디 (raw bytes)
        signature_header: X-Rosud-Signature 헤더 값
        secret: 웹훅 등록 시 사용한 시크릿 키
        max_age_seconds: 허용할 최대 요청 지연 시간 (기본 5분)

    Returns:
        True if valid, False otherwise
    """
    try:
        # 헤더 파싱
        parts = {k: v for k, v in (p.split("=", 1) for p in signature_header.split(","))}
        timestamp = int(parts.get("t", "0"))
        received_sig = parts.get("v1", "")
    except (ValueError, KeyError):
        return False

    # 타임스탬프 유효성 검증 (replay attack 방어)
    current_time = int(time.time())
    if abs(current_time - timestamp) > max_age_seconds:
        print(f"⚠️  웹훅 타임스탬프 만료: {abs(current_time - timestamp)}초 경과")
        return False

    # HMAC-SHA256 서명 계산
    signed_payload = f"{timestamp}.{payload_body.decode('utf-8')}".encode()
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    # 타이밍 공격 방어를 위한 상수시간 비교
    return hmac.compare_digest(expected_sig, received_sig)


# ──────────────────────────────────────────────────────────
# 3. 웹훅 이벤트 처리 패턴
# ──────────────────────────────────────────────────────────

def handle_payment_event(event_type: str, data: dict[str, Any]) -> None:
    """
    결제 이벤트 타입별 처리 핸들러

    Rosud 웹훅 이벤트 구조:
    {
        "type": "payment.confirmed",
        "created_at": "2024-03-15T12:00:00Z",
        "data": {
            "id": "uuid",
            "amount": "5.00",
            "currency": "USDC",
            "from_wallet": "0x...",
            "to_wallet": "0x...",
            "memo": "api_call_fee",
            "status": "confirmed",
            "tx_hash": "0x...",
            "confirmed_at": "2024-03-15T12:00:05Z"
        }
    }
    """
    payment_id = data.get("id", "unknown")
    amount = data.get("amount")
    currency = data.get("currency", "USDC")
    memo = data.get("memo", "")

    if event_type == "payment.confirmed":
        # 결제 완료 처리
        tx_hash = data.get("tx_hash")
        print(f"✅ 결제 완료: {payment_id}")
        print(f"   금액: {amount} {currency}")
        print(f"   메모: {memo}")
        print(f"   TX: {tx_hash}")

        # 예: DB 업데이트, 서비스 활성화, 영수증 발송 등
        # db.payments.update(payment_id, status="confirmed")
        # send_confirmation_email(data["from_wallet"], amount)

    elif event_type == "payment.failed":
        error = data.get("error", "unknown")
        print(f"❌ 결제 실패: {payment_id}")
        print(f"   사유: {error}")

        # 예: 실패 알림, 재시도 로직
        # notify_admin(f"Payment failed: {payment_id}, reason: {error}")

    elif event_type == "payment.pending":
        print(f"⏳ 결제 처리 중: {payment_id} ({amount} {currency})")

        # 예: 임시 서비스 활성화 (확정 전 낙관적 업데이트)

    else:
        print(f"⚠️  알 수 없는 이벤트: {event_type}")


# ──────────────────────────────────────────────────────────
# 4. FastAPI 웹훅 서버 예시
# ──────────────────────────────────────────────────────────

FASTAPI_SERVER_EXAMPLE = '''
"""
FastAPI 웹훅 서버 — 실제 서버 구현 예시

설치: pip install fastapi uvicorn rosud
실행: uvicorn webhook_server:app --host 0.0.0.0 --port 8000
"""
import hashlib
import hmac
import json
import os
import time

from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI()

ROSUD_WEBHOOK_SECRET = os.environ["ROSUD_WEBHOOK_SECRET"]


@app.post("/webhooks/rosud")
async def receive_rosud_webhook(
    request: Request,
    x_rosud_signature: str = Header(..., alias="X-Rosud-Signature"),
) -> dict:
    """Rosud 웹훅 수신 엔드포인트"""
    body = await request.body()

    # 서명 검증 (필수!)
    if not verify_signature(body, x_rosud_signature, ROSUD_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # 이벤트 파싱
    event = json.loads(body)
    event_type = event.get("type")
    data = event.get("data", {})

    # 이벤트 처리
    if event_type == "payment.confirmed":
        payment_id = data["id"]
        amount = data["amount"]
        # await db.confirm_payment(payment_id)
        print(f"Payment confirmed: {payment_id} ({amount} USDC)")

    elif event_type == "payment.failed":
        payment_id = data["id"]
        # await notify_failure(payment_id)
        print(f"Payment failed: {payment_id}")

    # Rosud에게 200 OK 반환 (빠르게!)
    return {"received": True}


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """HMAC-SHA256 서명 검증"""
    try:
        parts = {k: v for k, v in (p.split("=", 1) for p in signature.split(","))}
        timestamp = int(parts["t"])
        received_sig = parts["v1"]
    except (ValueError, KeyError):
        return False

    # 5분 이내 요청만 허용
    if abs(int(time.time()) - timestamp) > 300:
        return False

    signed = f"{timestamp}.{body.decode()}".encode()
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_sig)
'''


# ──────────────────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Rosud 웹훅 예시 ===\n")

    print("1. 웹훅 등록")
    print("-" * 40)
    setup_webhook()

    print("\n2. 웹훅 목록 조회")
    print("-" * 40)
    list_and_manage_webhooks()

    print("\n3. 서명 검증 테스트")
    print("-" * 40)
    # 테스트용 페이로드
    test_secret = "test-webhook-secret"
    test_payload = b'{"type":"payment.confirmed","data":{"id":"abc123","amount":"5.00"}}'
    test_timestamp = int(time.time())
    signed_str = f"{test_timestamp}.{test_payload.decode()}".encode()
    test_sig = hmac.new(test_secret.encode(), signed_str, hashlib.sha256).hexdigest()
    test_header = f"t={test_timestamp},v1={test_sig}"

    is_valid = verify_webhook_signature(test_payload, test_header, test_secret)
    print(f"서명 검증 결과: {'✅ 유효' if is_valid else '❌ 무효'}")

    print("\n4. 이벤트 처리 예시")
    print("-" * 40)
    handle_payment_event("payment.confirmed", {
        "id": "pay_test_001",
        "amount": "5.00",
        "currency": "USDC",
        "memo": "api_call_fee",
        "tx_hash": "0xabc123",
    })

    print("\n5. FastAPI 서버 예시 코드 (별도 파일로 실행 필요):")
    print("   → webhook_server.py 참고")
    print("   → 실행: uvicorn webhook_server:app --port 8000")
