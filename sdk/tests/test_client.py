"""클라이언트 초기화 및 기본 동작 테스트"""
import os
from unittest.mock import patch

import pytest

import rosud
from rosud import AsyncRosud, Rosud
from rosud.exceptions import AuthenticationError, RosudError


class TestRosudClientInit:
    """Rosud 클라이언트 초기화 테스트"""

    def test_init_with_api_key(self):
        client = Rosud(api_key="rosud_live_test_key")
        assert client._http._api_key == "rosud_live_test_key"

    def test_init_from_env_variable(self):
        with patch.dict(os.environ, {"ROSUD_API_KEY": "rosud_live_env_key"}):
            client = Rosud()
            assert client._http._api_key == "rosud_live_env_key"

    def test_init_without_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # ROSUD_API_KEY 환경변수도 없는 상태
            env = {k: v for k, v in os.environ.items() if k != "ROSUD_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="API 키가 필요합니다"):
                    Rosud()

    def test_init_with_custom_base_url(self):
        client = Rosud(api_key="test_key", base_url="https://api.rosud.com")
        assert client._http._base_url == "https://api.rosud.com"

    def test_base_url_trailing_slash_stripped(self):
        client = Rosud(api_key="test_key", base_url="https://api.rosud.com/")
        assert client._http._base_url == "https://api.rosud.com"

    def test_has_resource_attributes(self):
        client = Rosud(api_key="test_key")
        assert hasattr(client, "payments")
        assert hasattr(client, "agents")
        assert hasattr(client, "wallets")
        assert hasattr(client, "webhooks")

    def test_context_manager(self):
        with Rosud(api_key="test_key") as client:
            assert isinstance(client, Rosud)

    def test_repr(self):
        client = Rosud(api_key="test_key", base_url="https://api.rosud.com")
        assert "Rosud" in repr(client)
        assert "api.rosud.com" in repr(client)


class TestAsyncRosudClientInit:
    """AsyncRosud 클라이언트 초기화 테스트"""

    def test_init_with_api_key(self):
        client = AsyncRosud(api_key="rosud_live_test_key")
        assert client._http._api_key == "rosud_live_test_key"

    def test_has_resource_attributes(self):
        client = AsyncRosud(api_key="test_key")
        assert hasattr(client, "payments")
        assert hasattr(client, "agents")
        assert hasattr(client, "wallets")
        assert hasattr(client, "webhooks")

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with AsyncRosud(api_key="test_key") as client:
            assert isinstance(client, AsyncRosud)


class TestExceptions:
    """예외 클래스 테스트"""

    def test_rosud_error_attributes(self):
        err = RosudError(
            "테스트 오류",
            status_code=400,
            error_code="test_error",
            response_body={"error": "test_error", "message": "테스트 오류"},
        )
        assert err.message == "테스트 오류"
        assert err.status_code == 400
        assert err.error_code == "test_error"
        assert str(err) == "테스트 오류"

    def test_authentication_error_is_rosud_error(self):
        err = AuthenticationError("인증 실패", status_code=401)
        assert isinstance(err, RosudError)
        assert err.status_code == 401

    def test_validation_error_field_details(self):
        from rosud.exceptions import ValidationError

        err = ValidationError(
            "유효성 검사 실패",
            field_errors=[
                {"loc": ["body", "amount"], "msg": "must be greater than 0"},
            ],
        )
        assert "amount" in str(err)
        assert "must be greater than 0" in str(err)

    def test_rate_limit_error_retry_after(self):
        from rosud.exceptions import RateLimitError

        err = RateLimitError("너무 많은 요청", retry_after=60, status_code=429)
        assert err.retry_after == 60


class TestModels:
    """모델 테스트"""

    def test_payment_model(self):
        from datetime import datetime
        from decimal import Decimal

        from rosud.models import Payment

        payment = Payment(
            id="550e8400-e29b-41d4-a716-446655440000",
            amount=Decimal("5.00"),
            currency="USDC",
            network="base",
            to_wallet="0xRecipient",
            status="confirmed",
            created_at=datetime.now(),
        )
        assert payment.is_confirmed
        assert not payment.is_pending
        assert not payment.is_failed
        assert "Payment" in repr(payment)

    def test_payment_list_iterable(self):
        from datetime import datetime
        from decimal import Decimal

        from rosud.models import Payment, PaymentList

        payments = PaymentList(
            items=[
                Payment(
                    id="550e8400-e29b-41d4-a716-446655440000",
                    amount=Decimal("5.00"),
                    currency="USDC",
                    network="base",
                    to_wallet="0xRecipient",
                    status="confirmed",
                    created_at=datetime.now(),
                )
            ],
            total=1,
            limit=20,
            offset=0,
        )
        assert len(payments) == 1
        for p in payments:
            assert isinstance(p, Payment)
        assert payments[0].amount == Decimal("5.00")

    def test_wallet_balance_model(self):
        from decimal import Decimal

        from rosud.models import WalletBalance

        balance = WalletBalance(
            wallet_id="wallet-123",
            address="0xMyWallet",
            amount=Decimal("100.50"),
            currency="USDC",
            network="base",
        )
        assert balance.amount == Decimal("100.50")
        assert "100.50" in repr(balance)

    def test_agent_created_masks_key_in_repr(self):
        import uuid
        from datetime import datetime

        from rosud.models import AgentCreated

        agent = AgentCreated(
            id=uuid.uuid4(),
            operator_id=uuid.uuid4(),
            name="Test Bot",
            is_active=True,
            created_at=datetime.now(),
            api_key="rosud_live_supersecretkey",
        )
        r = repr(agent)
        # repr에서 full key가 노출되면 안 됨
        assert "supersecretkey" not in r
