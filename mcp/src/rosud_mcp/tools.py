"""Rosud MCP 도구 정의 - 4가지 결제 도구"""
import json
from typing import Any

from mcp.types import TextContent, Tool

from .client import RosudAPIError, RosudClient

# ─── 도구 스키마 정의 ─────────────────────────────────────────────────────────

CREATE_PAYMENT_TOOL = Tool(
    name="create_payment",
    description=(
        "USDC 스테이블코인으로 결제를 생성합니다. "
        "API 호출 비용, 서비스 이용료, 데이터 구매 등 AI 에이전트가 "
        "외부 서비스에 자율적으로 결제할 때 사용하세요. "
        "결제 전 get_balance로 잔액을 확인하는 것을 권장합니다. "
        "예: '이 API 사용료 5달러를 결제해줘', 'AI 서비스 이용료를 지불해줘'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "결제 금액 (USD 단위, 예: 5.00). 최소 0.01 USD.",
                "minimum": 0.01,
            },
            "to": {
                "type": "string",
                "description": (
                    "수신자 지갑 주소(0x로 시작하는 이더리움 주소) 또는 "
                    "등록된 merchant ID (예: 'merchant_123')"
                ),
            },
            "memo": {
                "type": "string",
                "description": (
                    "결제 메모 또는 용도 설명 (선택사항). "
                    "예: 'api_call_fee', 'data_purchase', 'service_subscription'"
                ),
            },
            "idempotency_key": {
                "type": "string",
                "description": (
                    "멱등성 키 (선택사항). 동일한 키로 중복 요청 시 같은 결과 반환. "
                    "재시도 안전성을 위해 UUID 형식 권장."
                ),
            },
        },
        "required": ["amount", "to"],
    },
)

GET_BALANCE_TOOL = Tool(
    name="get_balance",
    description=(
        "현재 USDC 잔액을 조회합니다. "
        "결제 전 잔액을 확인하거나, 에이전트의 현재 가용 자금을 파악할 때 사용하세요. "
        "예: '잔액이 얼마야?', '결제 가능한 금액을 알려줘'"
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
        "최근 결제 내역을 조회합니다. "
        "결제 이력 확인, 특정 상태의 결제 추적, 지출 내역 분석에 사용하세요. "
        "예: '최근 결제 내역을 보여줘', '실패한 결제가 있어?', '오늘 얼마 썼어?'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "조회할 결제 수 (기본값: 10, 최대: 100)",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
            },
            "status": {
                "type": "string",
                "description": (
                    "결제 상태 필터 (선택사항). "
                    "pending: 처리 중, confirmed: 완료, failed: 실패"
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
        "특정 결제의 상태와 상세 정보를 조회합니다. "
        "결제 완료 여부 확인, 트랜잭션 추적, 결제 세부 정보 확인에 사용하세요. "
        "예: '결제 pay_xxx 처리됐어?', '이 결제 확인해줘'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "payment_id": {
                "type": "string",
                "description": "조회할 결제 ID (예: 'pay_01HXXX...')",
            },
        },
        "required": ["payment_id"],
    },
)

ALL_TOOLS = [CREATE_PAYMENT_TOOL, GET_BALANCE_TOOL, LIST_PAYMENTS_TOOL, GET_PAYMENT_TOOL]


# ─── 도구 실행 핸들러 ─────────────────────────────────────────────────────────

def _format_result(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


def _format_error(error: Exception) -> list[TextContent]:
    if isinstance(error, RosudAPIError):
        msg = f"결제 API 오류 [{error.status_code}] {error.error}: {error.message}"
    elif isinstance(error, ValueError):
        msg = f"설정 오류: {error}"
    else:
        msg = f"예기치 않은 오류: {type(error).__name__}: {error}"
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
