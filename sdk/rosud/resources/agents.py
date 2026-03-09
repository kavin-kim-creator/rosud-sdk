"""에이전트 리소스"""
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
    """에이전트 API (동기)

    Examples:
        >>> agent = client.agents.create(
        ...     name="Payment Bot",
        ...     spending_limit_daily=100.00,
        ...     spending_limit_per_tx=10.00,
        ... )
        >>> print(agent.api_key)  # 최초 1회만 반환

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
        """새 에이전트를 생성합니다.

        Args:
            name: 에이전트 이름
            spending_limit_daily: 일별 지출 한도 (USDC, 선택)
            spending_limit_per_tx: 건별 지출 한도 (USDC, 선택)
            allowed_recipients: 허용된 수신자 주소 목록 (None = 모든 주소 허용)

        Returns:
            AgentCreated: 생성된 에이전트 (api_key 포함 - 최초 1회만 반환)

        Raises:
            ValidationError: 필수 파라미터 누락 또는 유효하지 않은 값
            AuthenticationError: API 키 오류
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
        """에이전트 목록을 조회합니다.

        Args:
            limit: 최대 반환 건수 (기본값: 20)
            offset: 건너뛸 건수 (기본값: 0)
            is_active: 활성 상태 필터 (선택)

        Returns:
            AgentList: 에이전트 목록 (이터러블)
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if is_active is not None:
            params["is_active"] = is_active
        data = self._http.get("/v1/agents", params=params)
        return AgentList.model_validate(data)

    def get(self, agent_id: str) -> Agent:
        """특정 에이전트를 조회합니다.

        Args:
            agent_id: 에이전트 UUID

        Returns:
            Agent: 에이전트 객체

        Raises:
            NotFoundError: 에이전트를 찾을 수 없는 경우
        """
        data = self._http.get(f"/v1/agents/{agent_id}")
        return Agent.model_validate(data)


class AsyncAgentsResource:
    """에이전트 API (비동기)"""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        spending_limit_daily: Optional[float | Decimal] = None,
        spending_limit_per_tx: Optional[float | Decimal] = None,
        allowed_recipients: Optional[list[str]] = None,
    ) -> AgentCreated:
        """새 에이전트를 생성합니다 (비동기)."""
        payload = _build_agent_payload(name, spending_limit_daily, spending_limit_per_tx, allowed_recipients)
        data = await self._http.post("/v1/agents", json=payload)
        return AgentCreated.model_validate(data)

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> AgentList:
        """에이전트 목록을 조회합니다 (비동기)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if is_active is not None:
            params["is_active"] = is_active
        data = await self._http.get("/v1/agents", params=params)
        return AgentList.model_validate(data)

    async def get(self, agent_id: str) -> Agent:
        """특정 에이전트를 조회합니다 (비동기)."""
        data = await self._http.get(f"/v1/agents/{agent_id}")
        return Agent.model_validate(data)
