"""
Async usage example - Rosud Python SDK

Example of using with asyncio or async frameworks (FastAPI, aiohttp, etc.)
"""
import asyncio
import os

import rosud
from rosud.exceptions import RosudError


async def single_payment_example() -> None:
    """Simple async payment example"""
    client = rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx"))

    try:
        payment = await client.payments.create(
            amount=1.00,
            to="0xRecipientAddress",
            memo="async_payment",
        )
        print(f"Payment complete: {payment.id} ({payment.status})")
    except RosudError as e:
        print(f"Payment error: {e.message}")
    finally:
        await client.aclose()


async def concurrent_payments_example() -> None:
    """Example of processing multiple payments concurrently (high performance)"""
    async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx")) as client:
        # Run multiple tasks in parallel
        balance_task = client.wallets.get_balance()
        payments_task = client.payments.list(limit=5)

        balance, payments = await asyncio.gather(balance_task, payments_task)

        print(f"Current balance: {balance.amount} USDC")
        print(f"Recent {len(payments)} payment(s):")
        for p in payments:
            print(f"  - {p.id}: {p.amount} USDC ({p.status})")


async def batch_payments_example() -> None:
    """Batch payment processing example"""
    recipients = [
        {"to": "0xRecipient1", "amount": 1.00, "memo": "service_fee_1"},
        {"to": "0xRecipient2", "amount": 2.50, "memo": "service_fee_2"},
        {"to": "0xRecipient3", "amount": 0.50, "memo": "service_fee_3"},
    ]

    async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx")) as client:
        # Process all payments concurrently
        tasks = [
            client.payments.create(
                amount=r["amount"],
                to=r["to"],
                memo=r["memo"],
                idempotency_key=f"batch-{i}",  # prevent duplicates
            )
            for i, r in enumerate(recipients)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Payment {i+1} failed: {result}")
            else:
                print(f"Payment {i+1} succeeded: {result.id} ({result.status})")


async def webhook_setup_example() -> None:
    """Webhook setup example"""
    async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx")) as client:
        try:
            webhook = await client.webhooks.create(
                url="https://myapp.com/webhooks/rosud",
                events=["payment.confirmed", "payment.failed"],
                secret="my-super-secret-hmac-key",
            )
            print(f"Webhook registered: {webhook.id}")
            print(f"URL: {webhook.url}")
            print(f"Subscribed events: {webhook.events}")
        except RosudError as e:
            print(f"Webhook registration failed: {e.message}")


async def main() -> None:
    print("=== Simple Payment ===")
    await single_payment_example()

    print("\n=== Concurrent Processing ===")
    await concurrent_payments_example()

    print("\n=== Batch Payments ===")
    await batch_payments_example()

    print("\n=== Webhook Setup ===")
    await webhook_setup_example()


if __name__ == "__main__":
    asyncio.run(main())
