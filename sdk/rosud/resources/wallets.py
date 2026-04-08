"""Wallet resource"""
from __future__ import annotations

from ..models import WalletBalance
from .._http import AsyncHTTPClient, SyncHTTPClient


class WalletsResource:
    """Wallets API (synchronous)

    Examples:
        >>> balance = client.wallets.get_balance()
        >>> print(f"Balance: {balance.amount} {balance.currency}")
        >>> print(f"Address: {balance.address}")
    """

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def get_balance(self) -> WalletBalance:
        """Retrieve the current wallet balance.

        Returns:
            WalletBalance: Balance info (amount, currency, network, address)

        Raises:
            AuthenticationError: API key error
        """
        data = self._http.get("/v1/wallets/balance")
        return WalletBalance.model_validate(data)


class AsyncWalletsResource:
    """Wallets API (asynchronous)

    Examples:
        >>> balance = await client.wallets.get_balance()
        >>> print(f"Balance: {balance.amount} {balance.currency}")
    """

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def get_balance(self) -> WalletBalance:
        """Retrieve the current wallet balance (async).

        Returns:
            WalletBalance: Balance info
        """
        data = await self._http.get("/v1/wallets/balance")
        return WalletBalance.model_validate(data)
