"""Rosud MCP tool definitions — 4 payment tools"""
import json
from typing import Any

from mcp.types import TextContent, Tool

from .client import RosudAPIError, RosudClient

# --- Tool schema definitions ─────────────────────────────────────────────────

CREATE_PAYMENT_TOOL = Tool(
    name="create_payment",
    description=(
        "Create a payment using USDC stablecoin. "
        "Use this when an AI agent needs to autonomously pay external services "
        "for API call fees, service charges, data purchases, etc. "
        "It is recommended to check the balance with get_balance before making a payment. "
        "Examples: 'Pay $5 for this API usage', 'Pay the AI service fee'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Payment amount (in USD, e.g., 5.00). Minimum 0.01 USD.",
                "minimum": 0.01,
            },
            "to": {
                "type": "string",
                "description": (
                    "Recipient wallet address (Ethereum address starting with 0x) or "
                    "a registered merchant ID (e.g., 'merchant_123')"
                ),
            },
            "memo": {
                "type": "string",
                "description": (
                    "Payment memo or description (optional). "
                    "Examples: 'api_call_fee', 'data_purchase', 'service_subscription'"
                ),
            },
            "idempotency_key": {
                "type": "string",
                "description": (
                    "Idempotency key (optional). Duplicate requests with the same key return the same result. "
                    "UUID format is recommended for safe retries."
                ),
            },
        },
        "required": ["amount", "to"],
    },
)

GET_BALANCE_TOOL = Tool(
    name="get_balance",
    description=(
        "Query the current USDC balance. "
        "Use this to check the balance before making a payment, or to determine the agent's available funds. "
        "Examples: 'What is my balance?', 'How much can I pay?'"
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

LIST_PAYMENTS_TOOL = Tool(
    name="list_payments",
    description=(
        "Query recent payment history. "
        "Use this for checking payment records, tracking payments by status, or analyzing spending. "
        "Examples: 'Show me recent payments', 'Are there any failed payments?', 'How much did I spend today?'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of payments to retrieve (default: 10, max: 100)",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
            },
            "status": {
                "type": "string",
                "description": (
                    "Payment status filter (optional). "
                    "pending: processing, confirmed: completed, failed: failed"
                ),
                "enum": ["pending", "confirmed", "failed"],
            },
        },
        "required": [],
    },
)

GET_PAYMENT_TOOL = Tool(
    name="get_payment",
    description=(
        "Query the status and details of a specific payment. "
        "Use this to check payment completion, track transactions, or review payment details. "
        "Examples: 'Was payment pay_xxx processed?', 'Check this payment for me'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "payment_id": {
                "type": "string",
                "description": "Payment ID to query (e.g., 'pay_01HXXX...')",
            },
        },
        "required": ["payment_id"],
    },
)

ALL_TOOLS = [CREATE_PAYMENT_TOOL, GET_BALANCE_TOOL, LIST_PAYMENTS_TOOL, GET_PAYMENT_TOOL]


# --- Tool execution handlers ─────────────────────────────────────────────────

def _format_result(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


def _format_error(error: Exception) -> list[TextContent]:
    if isinstance(error, RosudAPIError):
        msg = f"Payment API error [{error.status_code}] {error.error}: {error.message}"
    elif isinstance(error, ValueError):
        msg = f"Configuration error: {error}"
    else:
        msg = f"Unexpected error: {type(error).__name__}: {error}"
    return [TextContent(type="text", text=msg)]


async def handle_create_payment(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = RosudClient()
        result = await client.create_payment(
            amount=float(arguments["amount"]),
            to=str(arguments["to"]),
            memo=arguments.get("memo"),
            idempotency_key=arguments.get("idempotency_key"),
        )
        return _format_result(result)
    except Exception as e:
        return _format_error(e)


async def handle_get_balance(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = RosudClient()
        result = await client.get_balance()
        return _format_result(result)
    except Exception as e:
        return _format_error(e)


async def handle_list_payments(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = RosudClient()
        result = await client.list_payments(
            limit=int(arguments.get("limit", 10)),
            status=arguments.get("status"),
        )
        return _format_result(result)
    except Exception as e:
        return _format_error(e)


async def handle_get_payment(arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = RosudClient()
        result = await client.get_payment(payment_id=str(arguments["payment_id"]))
        return _format_result(result)
    except Exception as e:
        return _format_error(e)


TOOL_HANDLERS = {
    "create_payment": handle_create_payment,
    "get_balance": handle_get_balance,
    "list_payments": handle_list_payments,
    "get_payment": handle_get_payment,
}
