"""
AutoGen integration example - Rosud Python SDK

Example integrating the Microsoft AutoGen framework with Rosud to allow
AI agents to autonomously process USDC payments.

Installation:
    pip install rosud-python pyautogen
"""
import os
from typing import Annotated, Optional

import rosud
from rosud.exceptions import PaymentError, RosudError

# Initialize Rosud client
client = rosud.Rosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx"))


# ──────────────────────────────────────────────────────────
# AutoGen function definitions (functions agents will call)
# ──────────────────────────────────────────────────────────

def make_payment(
    amount: Annotated[float, "Payment amount in USDC"],
    recipient: Annotated[str, "Recipient wallet address (0x...)"],
    memo: Annotated[str, "Payment memo or description"] = "",
) -> str:
    """Make a USDC payment via Rosud.

    This function allows an AI agent to make cryptocurrency payments
    in USDC on the Base L2 network.
    """
    try:
        payment = client.payments.create(
            amount=amount,
            to=recipient,
            memo=memo or "autogen_payment",
        )
        return (
            f"Payment successful!\n"
            f"  ID: {payment.id}\n"
            f"  Amount: {payment.amount} USDC\n"
            f"  Recipient: {payment.to_wallet}\n"
            f"  Status: {payment.status}\n"
            f"  TX Hash: {payment.tx_hash or 'pending'}"
        )
    except PaymentError as e:
        return f"Payment failed: {e.message} (code: {e.error_code})"
    except RosudError as e:
        return f"Error: {e.message}"


def get_balance() -> str:
    """Get current USDC wallet balance."""
    try:
        balance = client.wallets.get_balance()
        return (
            f"Wallet Balance:\n"
            f"  Amount: {balance.amount} {balance.currency}\n"
            f"  Network: {balance.network}\n"
            f"  Address: {balance.address}"
        )
    except RosudError as e:
        return f"Error getting balance: {e.message}"


def get_payment_history(limit: Annotated[int, "Number of payments to retrieve"] = 5) -> str:
    """Get recent payment history."""
    try:
        payments = client.payments.list(limit=limit)
        if not payments.items:
            return "No payments found."

        lines = [f"Recent {len(payments)} payment(s) (total: {payments.total}):"]
        for p in payments:
            lines.append(
                f"  [{p.status.upper()}] {p.amount} USDC → "
                f"{p.to_wallet[:12]}... | {p.created_at:%Y-%m-%d %H:%M}"
            )
        return "\n".join(lines)
    except RosudError as e:
        return f"Error: {e.message}"


# ──────────────────────────────────────────────────────────
# AutoGen agent execution example
# ──────────────────────────────────────────────────────────

def run_autogen_example() -> None:
    """AutoGen ConversableAgent example"""
    try:
        import autogen
        from autogen import ConversableAgent, UserProxyAgent

        # LLM configuration
        llm_config = {
            "config_list": [
                {
                    "model": "gpt-4",
                    "api_key": os.environ.get("OPENAI_API_KEY"),
                }
            ],
            "temperature": 0,
        }

        # AI agent (handles payment processing)
        payment_agent = ConversableAgent(
            name="PaymentAgent",
            system_message=(
                "You are a payment processing agent. "
                "You can check wallet balances and make USDC payments. "
                "Always check the balance before making payments. "
                "Be careful and confirm the recipient address before paying."
            ),
            llm_config=llm_config,
        )

        # Register functions
        payment_agent.register_for_llm(name="make_payment", description="Make a USDC payment")(make_payment)
        payment_agent.register_for_llm(name="get_balance", description="Check wallet balance")(get_balance)
        payment_agent.register_for_llm(name="get_payment_history", description="Get payment history")(get_payment_history)

        # UserProxy (function executor)
        user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
        )

        user_proxy.register_for_execution(name="make_payment")(make_payment)
        user_proxy.register_for_execution(name="get_balance")(get_balance)
        user_proxy.register_for_execution(name="get_payment_history")(get_payment_history)

        # Start conversation
        user_proxy.initiate_chat(
            payment_agent,
            message=(
                "Please check my wallet balance and show me the last 3 payments. "
                "If my balance is over 10 USDC, pay 1.50 USDC to "
                "0xServiceProvider123 with memo 'autogen_test'. "
                "Reply TERMINATE when done."
            ),
        )

    except ImportError:
        print("AutoGen is not installed. Run: pip install pyautogen")
        print("\nDirect function test:")
        print(get_balance())
        print("\n" + get_payment_history(3))


# ──────────────────────────────────────────────────────────
# AutoGen v0.4+ (new API) example
# ──────────────────────────────────────────────────────────

def run_autogen_v04_example() -> None:
    """AutoGen v0.4+ AssistantAgent example"""
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.ui import Console
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        # Tool functions
        async def async_get_balance() -> str:
            async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY")) as c:
                balance = await c.wallets.get_balance()
                return f"{balance.amount} {balance.currency} on {balance.network}"

        async def async_make_payment(amount: float, to: str, memo: str = "") -> str:
            async with rosud.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY")) as c:
                payment = await c.payments.create(amount=amount, to=to, memo=memo)
                return f"Payment {payment.id}: {payment.status} ({payment.amount} USDC)"

        model_client = OpenAIChatCompletionClient(model="gpt-4o")

        agent = AssistantAgent(
            "payment_agent",
            model_client=model_client,
            tools=[async_get_balance, async_make_payment],
            system_message=(
                "You are a payment agent. "
                "Use the available tools to check balance and make payments."
            ),
        )

        import asyncio
        asyncio.run(Console(agent.run_stream(task="Check my USDC balance")))

    except ImportError:
        print("autogen-agentchat is not installed.")


if __name__ == "__main__":
    print("=== AutoGen + Rosud Integration Example ===\n")
    run_autogen_example()
