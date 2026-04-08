"""Rosud MCP Server tests"""
import json
import os
from unittest.mock import AsyncMock, patch

import pytest

os.environ.setdefault("ROSUD_API_KEY", "rosud_live_test_key_for_testing")
os.environ.setdefault("ROSUD_API_URL", "http://localhost:8000")


from rosud_mcp.client import RosudAPIError, RosudClient
from rosud_mcp.tools import (
    handle_create_payment,
    handle_get_balance,
    handle_get_payment,
    handle_list_payments,
)


# --- Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_payment_response():
    return {
        "id": "pay_01HXABCDEF",
        "status": "confirmed",
        "amount": "5.00",
        "currency": "USDC",
        "to": "0xRecipientAddress",
        "memo": "api_call_fee",
        "tx_hash": "0xTxHash",
        "created_at": "2026-03-03T00:00:00Z",
    }


@pytest.fixture
def mock_balance_response():
    return {
        "balance": "100.00",
        "currency": "USDC",
        "wallet_address": "0xAgentWallet",
        "network": "base",
    }


@pytest.fixture
def mock_payments_list_response():
    return {
        "payments": [
            {
                "id": "pay_01HXABCDEF",
                "status": "confirmed",
                "amount": "5.00",
                "currency": "USDC",
                "created_at": "2026-03-03T00:00:00Z",
            }
        ],
        "total": 1,
    }


# --- create_payment tests ────────────────────────────────────────────────────

class TestCreatePayment:
    async def test_create_payment_success(self, mock_payment_response):
        with patch.object(RosudClient, "create_payment", new_callable=AsyncMock) as mock:
            mock.return_value = mock_payment_response

            result = await handle_create_payment(
                {"amount": 5.00, "to": "0xRecipientAddress", "memo": "api_call_fee"}
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == "pay_01HXABCDEF"
        assert data["status"] == "confirmed"
        assert data["amount"] == "5.00"

    async def test_create_payment_with_idempotency_key(self, mock_payment_response):
        with patch.object(RosudClient, "create_payment", new_callable=AsyncMock) as mock:
            mock.return_value = mock_payment_response

            result = await handle_create_payment(
                {
                    "amount": 5.00,
                    "to": "0xRecipientAddress",
                    "idempotency_key": "unique-key-123",
                }
            )

        mock.assert_called_once_with(
            amount=5.00,
            to="0xRecipientAddress",
            memo=None,
            idempotency_key="unique-key-123",
        )
        assert len(result) == 1

    async def test_create_payment_api_error(self):
        with patch.object(RosudClient, "create_payment", new_callable=AsyncMock) as mock:
            mock.side_effect = RosudAPIError(402, "insufficient_balance", "Insufficient balance")

            result = await handle_create_payment(
                {"amount": 999999.00, "to": "0xRecipientAddress"}
            )

        assert len(result) == 1
        assert "402" in result[0].text
        assert "insufficient_balance" in result[0].text
        assert "Insufficient balance" in result[0].text

    async def test_create_payment_missing_api_key(self):
        with patch("rosud_mcp.tools.RosudClient") as MockClient:
            MockClient.side_effect = ValueError("ROSUD_API_KEY environment variable is not set")

            result = await handle_create_payment({"amount": 5.00, "to": "0xRecipient"})

        assert "Configuration error" in result[0].text


# --- get_balance tests ───────────────────────────────────────────────────────

class TestGetBalance:
    async def test_get_balance_success(self, mock_balance_response):
        with patch.object(RosudClient, "get_balance", new_callable=AsyncMock) as mock:
            mock.return_value = mock_balance_response

            result = await handle_get_balance({})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["balance"] == "100.00"
        assert data["currency"] == "USDC"

    async def test_get_balance_api_error(self):
        with patch.object(RosudClient, "get_balance", new_callable=AsyncMock) as mock:
            mock.side_effect = RosudAPIError(401, "unauthorized", "Invalid API key")

            result = await handle_get_balance({})

        assert "401" in result[0].text
        assert "unauthorized" in result[0].text


# --- list_payments tests ─────────────────────────────────────────────────────

class TestListPayments:
    async def test_list_payments_success(self, mock_payments_list_response):
        with patch.object(RosudClient, "list_payments", new_callable=AsyncMock) as mock:
            mock.return_value = mock_payments_list_response

            result = await handle_list_payments({"limit": 10})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["total"] == 1
        assert len(data["payments"]) == 1

    async def test_list_payments_with_status_filter(self, mock_payments_list_response):
        with patch.object(RosudClient, "list_payments", new_callable=AsyncMock) as mock:
            mock.return_value = mock_payments_list_response

            result = await handle_list_payments({"limit": 5, "status": "confirmed"})

        mock.assert_called_once_with(limit=5, status="confirmed")

    async def test_list_payments_default_limit(self, mock_payments_list_response):
        with patch.object(RosudClient, "list_payments", new_callable=AsyncMock) as mock:
            mock.return_value = mock_payments_list_response

            result = await handle_list_payments({})

        mock.assert_called_once_with(limit=10, status=None)


# --- get_payment tests ───────────────────────────────────────────────────────

class TestGetPayment:
    async def test_get_payment_success(self, mock_payment_response):
        with patch.object(RosudClient, "get_payment", new_callable=AsyncMock) as mock:
            mock.return_value = mock_payment_response

            result = await handle_get_payment({"payment_id": "pay_01HXABCDEF"})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == "pay_01HXABCDEF"

    async def test_get_payment_not_found(self):
        with patch.object(RosudClient, "get_payment", new_callable=AsyncMock) as mock:
            mock.side_effect = RosudAPIError(404, "payment_not_found", "Payment not found")

            result = await handle_get_payment({"payment_id": "pay_nonexistent"})

        assert "404" in result[0].text
        assert "payment_not_found" in result[0].text


# --- Tool definitions tests ──────────────────────────────────────────────────

class TestToolDefinitions:
    def test_all_tools_defined(self):
        from rosud_mcp.tools import ALL_TOOLS

        tool_names = {t.name for t in ALL_TOOLS}
        assert "create_payment" in tool_names
        assert "get_balance" in tool_names
        assert "list_payments" in tool_names
        assert "get_payment" in tool_names

    def test_create_payment_schema(self):
        from rosud_mcp.tools import CREATE_PAYMENT_TOOL

        schema = CREATE_PAYMENT_TOOL.inputSchema
        assert "amount" in schema["properties"]
        assert "to" in schema["properties"]
        assert schema["required"] == ["amount", "to"]

    def test_get_payment_schema(self):
        from rosud_mcp.tools import GET_PAYMENT_TOOL

        schema = GET_PAYMENT_TOOL.inputSchema
        assert "payment_id" in schema["properties"]
        assert "payment_id" in schema["required"]

    def test_all_tools_have_description(self):
        from rosud_mcp.tools import ALL_TOOLS

        for tool in ALL_TOOLS:
            assert tool.description, f"Tool {tool.name} has no description"
            assert len(tool.description) > 20, f"Tool {tool.name} description is too short"
