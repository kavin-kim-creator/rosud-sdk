"""
LangChain Tool integration example - Rosud Python SDK

Example of an AI agent autonomously processing USDC payments as a LangChain Tool.

Installation:
    pip install rosud-python langchain langchain-openai
"""
import os
from typing import Optional

# ──────────────────────────────────────────────────────────
# Method 1: @tool decorator (simple usage)
# ──────────────────────────────────────────────────────────
try:
    from langchain.tools import tool
    from rosud import Rosud
    from rosud.exceptions import PaymentError, RosudError

    rosud_client = Rosud(api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_xxx"))

    @tool
    def pay_for_service(amount: float, to: str, memo: str = "") -> str:
        """Pay for an AI service using USDC stablecoin via Rosud.

        Use this tool when you need to make a payment for a service.
        Payments are made in USDC on the Base L2 network.

        Args:
            amount: Payment amount in USDC (e.g., 5.00)
            to: Recipient wallet address (0x...)
            memo: Optional memo/description for the payment

        Returns:
            Payment status as a string
        """
        try:
            payment = rosud_client.payments.create(
                amount=amount,
                to=to,
                memo=memo or "langchain_agent_payment",
            )
            return (
                f"Payment {payment.id}: {payment.status} "
                f"({payment.amount} USDC → {payment.to_wallet[:10]}...)"
            )
        except PaymentError as e:
            return f"Payment failed [{e.error_code}]: {e.message}"
        except RosudError as e:
            return f"Error: {e.message}"

    @tool
    def check_wallet_balance() -> str:
        """Check the current USDC wallet balance.

        Use this before making payments to ensure sufficient funds.

        Returns:
            Current balance as a string
        """
        try:
            balance = rosud_client.wallets.get_balance()
            return f"Balance: {balance.amount} {balance.currency} on {balance.network}"
        except RosudError as e:
            return f"Error checking balance: {e.message}"

    @tool
    def list_recent_payments(limit: int = 5) -> str:
        """List recent payments made through Rosud.

        Args:
            limit: Number of recent payments to retrieve (max 20)

        Returns:
            Recent payments as formatted string
        """
        try:
            payments = rosud_client.payments.list(limit=min(limit, 20))
            if not payments.items:
                return "No payments found."
            lines = [f"Recent {len(payments)} payment(s):"]
            for p in payments:
                lines.append(f"  - {p.id}: {p.amount} USDC ({p.status})")
            return "\n".join(lines)
        except RosudError as e:
            return f"Error listing payments: {e.message}"

except ImportError:
    print("LangChain is not installed. Run: pip install langchain")


# ──────────────────────────────────────────────────────────
# Method 2: BaseTool subclass (advanced usage, more control)
# ──────────────────────────────────────────────────────────
try:
    from langchain.tools import BaseTool
    from pydantic import BaseModel, Field
    from rosud import Rosud
    from rosud.exceptions import RosudError

    class PaymentInput(BaseModel):
        amount: float = Field(..., description="Payment amount in USDC", gt=0)
        to: str = Field(..., description="Recipient wallet address (0x...)")
        memo: Optional[str] = Field(None, description="Optional memo for the payment")

    class RosudPaymentTool(BaseTool):
        """LangChain Tool for making USDC payments via Rosud."""

        name: str = "rosud_payment"
        description: str = (
            "Make a USDC payment to a recipient address. "
            "Use this for paying AI services, API fees, or any service requiring USDC payment. "
            "Payments are on the Base L2 network."
        )
        args_schema: type[BaseModel] = PaymentInput

        _client: Rosud = None  # type: ignore[assignment]

        def __init__(self, api_key: Optional[str] = None, **kwargs):
            super().__init__(**kwargs)
            object.__setattr__(self, '_client', Rosud(api_key=api_key))

        def _run(self, amount: float, to: str, memo: Optional[str] = None) -> str:
            try:
                payment = self._client.payments.create(
                    amount=amount,
                    to=to,
                    memo=memo or "langchain_payment",
                )
                return f"✅ Payment successful: {payment.id} | {payment.amount} USDC | Status: {payment.status}"
            except RosudError as e:
                return f"❌ Payment failed: {e.message} (code: {e.error_code})"

        async def _arun(self, amount: float, to: str, memo: Optional[str] = None) -> str:
            import rosud as r
            async with r.AsyncRosud(api_key=os.environ.get("ROSUD_API_KEY")) as client:
                try:
                    payment = await client.payments.create(
                        amount=amount,
                        to=to,
                        memo=memo or "langchain_async_payment",
                    )
                    return f"✅ Payment successful: {payment.id} | {payment.amount} USDC | Status: {payment.status}"
                except RosudError as e:
                    return f"❌ Payment failed: {e.message}"

except ImportError:
    pass


# ──────────────────────────────────────────────────────────
# LangChain Agent execution example
# ──────────────────────────────────────────────────────────
def run_langchain_agent_example() -> None:
    """LangChain ReAct agent example"""
    try:
        from langchain.agents import AgentType, initialize_agent
        from langchain_openai import ChatOpenAI

        # Define tools
        tools = [pay_for_service, check_wallet_balance, list_recent_payments]

        # LLM configuration
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        # Initialize ReAct agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
        )

        # Run the agent
        result = agent.run(
            "Check my USDC balance and if I have enough funds, "
            "pay 2.50 USDC to 0xServiceProvider for data analysis service."
        )
        print(f"\nAgent result: {result}")

    except ImportError as e:
        print(f"Required packages are missing: {e}")
        print("Run: pip install langchain langchain-openai")


if __name__ == "__main__":
    run_langchain_agent_example()
