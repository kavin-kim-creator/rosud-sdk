"""Agent resource"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from ..models import Agent, AgentCreated, AgentList
from .._http import AsyncHTTPClient, SyncHTTPClient


def _build_agent_payload(
    name: str,
    spending_limit_daily: Optional[float | Decimal] = None,
    spending_limit_per_tx: Optional[float | Decimal] = None,
    allowed_recipients: Optional[list[str]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name}
    if spending_limit_daily is not None:
        payload["spending_limit_daily"] = str(Decimal(str(spending_limit_daily)))
    if spending_limit_per_tx is not None:
        payload["spending_limit_per_tx"] = str(Decimal(str(spending_limit_per_tx)))
    if allowed_recipients is not None:
        payload["allowed_recipients"] = allowed_recipients
    return payload


class AgentsResource:
    """Agents API (synchronous)

    Examples:
        >>> agent = client.agents.create(
        ...     name="Payment Bot",
        ...     spending_limit_daily=100.00,
        ...     spending_limit_per_tx=10.00,
        ... )
        >>> print(agent.api_key)  # returned only once

        >>> agents = client.agents.list()
        >>> for a in agents:
        ...     print(a.id, a.name, a.is_active)
    """

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        spending_limit_daily: Optional[float | Decimal] = None,
        spending_limit_per_tx: Optional[float | Decimal] = None,
        allowed_recipients: Optional[list[str]] = None,
    ) -> AgentCreated:
        """Create a new agent.

        Args:
            name: Agent name
            spending_limit_daily: Daily spending limit in USDC (optional)
            spending_limit_per_tx: Per-transaction spending limit in USDC (optional)
            allowed_recipients: List of allowed recipient addresses (None = all addresses allowed)

        Returns:
            AgentCreated: The created agent (includes api_key — returned only once)

        Raises:
            ValidationError: Missing required parameter or invalid value
            AuthenticationError: API key error
        """
        payload = _build_agent_payload(name, spending_limit_daily, spending_limit_per_tx, allowed_recipients)
        data = self._http.post("/v1/agents", json=payload)
        return AgentCreated.model_validate(data)

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> AgentList:
        """List agents.

        Args:
            limit: Maximum number of results to return (default: 20)
            offset: Number of results to skip (default: 0)
            is_active: Active status filter (optional)

        Returns:
            AgentList: List of agents (iterable)
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if is_active is not None:
            params["is_active"] = is_active
        data = self._http.get("/v1/agents", params=params)
        return AgentList.model_validate(data)

    def get(self, agent_id: str) -> Agent:
        """Retrieve a specific agent.

        Args:
            agent_id: Agent UUID

        Returns:
            Agent: The agent object

        Raises:
            NotFoundError: If the agent is not found
        """
        data = self._http.get(f"/v1/agents/{agent_id}")
        return Agent.model_validate(data)


class AsyncAgentsResource:
    """Agents API (asynchronous)"""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        spending_limit_daily: Optional[float | Decimal] = None,
        spending_limit_per_tx: Optional[float | Decimal] = None,
        allowed_recipients: Optional[list[str]] = None,
    ) -> AgentCreated:
        """Create a new agent (async)."""
        payload = _build_agent_payload(name, spending_limit_daily, spending_limit_per_tx, allowed_recipients)
        data = await self._http.post("/v1/agents", json=payload)
        return AgentCreated.model_validate(data)

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> AgentList:
        """List agents (async)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if is_active is not None:
            params["is_active"] = is_active
        data = await self._http.get("/v1/agents", params=params)
        return AgentList.model_validate(data)

    async def get(self, agent_id: str) -> Agent:
        """Retrieve a specific agent (async)."""
        data = await self._http.get(f"/v1/agents/{agent_id}")
        return Agent.model_validate(data)
