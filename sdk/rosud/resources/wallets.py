"""지갑 리소스"""
from __future__ import annotations

from ..models import WalletBalance
from .._http import AsyncHTTPClient, SyncHTTPClient


class WalletsResource:
    """지갑 API (동기)

    Examples:
        >>> balance = client.wallets.get_balance()
        >>> print(f"잔액: {balance.amount} {balance.currency}")
        >>> print(f"주소: {balance.address}")
    """

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def get_balance(self) -> WalletBalance:
        """현재 지갑 잔액을 조회합니다.

        Returns:
            WalletBalance: 잔액 정보 (금액, 통화, 네트워크, 주소)

        Raises:
            AuthenticationError: API 키 오류
        """
        data = self._http.get("/v1/wallets/balance")
        return WalletBalance.model_validate(data)


class AsyncWalletsResource:
    """지갑 API (비동기)

    Examples:
        >>> balance = await client.wallets.get_balance()
        >>> print(f"잔액: {balance.amount} {balance.currency}")
    """

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_balance(self) -> WalletBalance:
        """현재 지갑 잔액을 조회합니다 (비동기).

        Returns:
            WalletBalance: 잔액 정보
        """
        data = await self._http.get("/v1/wallets/balance")
        return WalletBalance.model_validate(data)
