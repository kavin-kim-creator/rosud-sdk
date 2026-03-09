"""
비동기 사용 예시 - Rosud Python SDK

asyncio 또는 비동기 프레임워크(FastAPI, aiohttp 등)와 함께 사용하는 예시
"""
import asyncio
import os

import rosud
from rosud.exceptions import RosudError


async def single_payment_example() -> None:
    """단순 비동기 결제 예시"""
    client = rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx"))

    try:
        payment = await client.payments.create(
            amount=1.00,
            to="0xRecipientAddress",
            memo="async_payment",
        )
        print(f"결제 완료: {payment.id} ({payment.status})")
    except RosudError as e:
        print(f"결제 오류: {e.message}")
    finally:
        await client.aclose()


async def concurrent_payments_example() -> None:
    """여러 결제를 동시에 처리하는 예시 (고성능)"""
    async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx")) as client:
        # 병렬로 여러 작업 실행
        balance_task = client.wallets.get_balance()
        payments_task = client.payments.list(limit=5)

        balance, payments = await asyncio.gather(balance_task, payments_task)

        print(f"현재 잔액: {balance.amount} USDC")
        print(f"최근 결제 {len(payments)}건:")
        for p in payments:
            print(f"  - {p.id}: {p.amount} USDC ({p.status})")


async def batch_payments_example() -> None:
    """배치 결제 처리 예시"""
    recipients = [
        {"to": "0xRecipient1", "amount": 1.00, "memo": "service_fee_1"},
        {"to": "0xRecipient2", "amount": 2.50, "memo": "service_fee_2"},
        {"to": "0xRecipient3", "amount": 0.50, "memo": "service_fee_3"},
    ]

    async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx")) as client:
        # 모든 결제를 동시에 처리
        tasks = [
            client.payments.create(
                amount=r["amount"],
                to=r["to"],
                memo=r["memo"],
                idempotency_key=f"batch-{i}",  # 중복 방지
            )
            for i, r in enumerate(recipients)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"결제 {i+1} 실패: {result}")
            else:
                print(f"결제 {i+1} 성공: {result.id} ({result.status})")


async def webhook_setup_example() -> None:
    """웹훅 설정 예시"""
    async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx")) as client:
        try:
            webhook = await client.webhooks.create(
                url="https://myapp.com/webhooks/rosud",
                events=["payment.confirmed", "payment.failed"],
                secret="my-super-secret-hmac-key",
            )
            print(f"웹훅 등록 완료: {webhook.id}")
            print(f"URL: {webhook.url}")
            print(f"구독 이벤트: {webhook.events}")
        except RosudError as e:
            print(f"웹훅 등록 실패: {e.message}")


async def main() -> None:
    print("=== 단순 결제 ===")
    await single_payment_example()

    print("\n=== 병렬 처리 ===")
    await concurrent_payments_example()

    print("\n=== 배치 결제 ===")
    await batch_payments_example()

    print("\n=== 웹훅 설정 ===")
    await webhook_setup_example()


if __name__ == "__main__":
    asyncio.run(main())
