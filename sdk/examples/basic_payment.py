"""
Basic payment example - Rosud Python SDK

This example demonstrates the basic usage of the Rosud SDK:
- Creating a payment
- Listing payments
- Checking wallet balance
- Creating an agent
"""
import os

import rosud
from rosud.exceptions import InsufficientFundsError, PaymentError, RosudError


def main() -> None:
    # Set API key (via environment variable or directly)
    client = rosud.Rosud(
        api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_your_key_here"),
        base_url=os.environ.get("ROSUD_BASE_URL", "https://api.rosud.com"),
    )

    # ──────────────────────────────────────────────
    # 1. Check wallet balance
    # ──────────────────────────────────────────────
    print("=== Wallet Balance ===")
    try:
        balance = client.wallets.get_balance()
        print(f"Balance: {balance.amount} {balance.currency}")
        print(f"Address: {balance.address}")
        print(f"Network: {balance.network}")
    except RosudError as e:
        print(f"Balance check failed: {e.message}")

    # ──────────────────────────────────────────────
    # 2. Create a payment
    # ──────────────────────────────────────────────
    print("\n=== Create Payment ===")
    try:
        payment = client.payments.create(
            amount=5.00,
            currency="USDC",
            to="0xRecipientWalletAddress123456789012345678",
            memo="api_call_fee",
            idempotency_key="unique-payment-key-001",  # prevent duplicates
        )
        print(f"Payment ID: {payment.id}")
        print(f"Status: {payment.status}")
        print(f"Amount: {payment.amount} {payment.currency}")
        print(f"Recipient: {payment.to_wallet}")
        print(f"TX Hash: {payment.tx_hash or '(pending)'}")
    except InsufficientFundsError:
        print("Insufficient balance.")
    except PaymentError as e:
        print(f"Payment error [{e.error_code}]: {e.message}")
    except RosudError as e:
        print(f"Error: {e.message}")

    # ──────────────────────────────────────────────
    # 3. List payments
    # ──────────────────────────────────────────────
    print("\n=== Recent Payment List ===")
    try:
        payments = client.payments.list(limit=10)
        print(f"Showing {len(payments)} of {payments.total} total")
        for p in payments:
            print(f"  - {p.id} | {p.amount} USDC | {p.status} | {p.created_at:%Y-%m-%d %H:%M}")
    except RosudError as e:
        print(f"Payment list failed: {e.message}")

    # ──────────────────────────────────────────────
    # 4. Create an agent (sub-account for AI agents)
    # ──────────────────────────────────────────────
    print("\n=== Create Agent ===")
    try:
        agent = client.agents.create(
            name="Payment Bot v1",
            spending_limit_daily=100.00,      # daily limit: 100 USDC
            spending_limit_per_tx=10.00,       # per-tx limit: 10 USDC
            allowed_recipients=[               # whitelist (security)
                "0xApprovedRecipient1",
                "0xApprovedRecipient2",
            ],
        )
        print(f"Agent ID: {agent.id}")
        print(f"Agent name: {agent.name}")
        print(f"API key: {agent.api_key}")  # returned only once!
        print("⚠️  Store the API key securely. It cannot be retrieved again.")
    except RosudError as e:
        print(f"Agent creation failed: {e.message}")

    # ──────────────────────────────────────────────
    # 5. Context manager usage
    # ──────────────────────────────────────────────
    print("\n=== Context Manager Usage ===")
    with rosud.Rosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_key")) as c:
        try:
            balance = c.wallets.get_balance()
            print(f"Balance: {balance.amount} USDC")
        except RosudError as e:
            print(f"Error: {e}")

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
