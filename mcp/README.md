# Rosud MCP Server

Claude 에이전트가 USDC 스테이블코인으로 **자율 결제**를 실행할 수 있는 MCP(Model Context Protocol) 서버입니다.

## 제공 도구

| 도구 | 설명 |
|------|------|
| `create_payment` | USDC로 결제 생성 |
| `get_balance` | 현재 USDC 잔액 조회 |
| `list_payments` | 결제 내역 목록 조회 |
| `get_payment` | 특정 결제 상태 조회 |

## 설치

```bash
# 패키지 설치
pip install -e "packages/mcp[dev]"

# 또는 uv 사용
uv pip install -e "packages/mcp"
```

## 환경변수 설정

```bash
# 필수: Rosud API Key
export ROSUD_API_KEY=rosud_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 선택: API URL (기본값: http://localhost:8000)
export ROSUD_API_URL=https://api.rosud.io
```

API Key는 Rosud 대시보드에서 발급받을 수 있습니다.

## Claude Desktop에 추가하기

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) 또는
`%APPDATA%\Claude\claude_desktop_config.json` (Windows)에 아래 내용을 추가하세요.

```json
{
  "mcpServers": {
    "rosud": {
      "command": "rosud-mcp",
      "env": {
        "ROSUD_API_KEY": "rosud_live_your_api_key_here",
        "ROSUD_API_URL": "https://api.rosud.io"
      }
    }
  }
}
```

`rosud-mcp` 커맨드가 PATH에 없는 경우 절대 경로를 사용하세요:

```json
{
  "mcpServers": {
    "rosud": {
      "command": "/path/to/venv/bin/rosud-mcp",
      "env": {
        "ROSUD_API_KEY": "rosud_live_your_api_key_here"
      }
    }
  }
}
```

## 사용 예시

Claude Desktop에서 다음과 같이 요청할 수 있습니다:

### 잔액 확인
```
현재 USDC 잔액이 얼마야?
```

### 결제 실행
```
0x742d35Cc6634C0532925a3b844Bc454e4438f44e 주소로 API 호출 비용 5달러를 결제해줘.
메모는 'gpt4_api_call' 로 남겨줘.
```

### 결제 내역 조회
```
최근 10건의 결제 내역을 보여줘.
실패한 결제가 있으면 알려줘.
```

### 결제 상태 확인
```
결제 pay_01HXABCDEF 처리됐어?
```

### 복합 워크플로우
```
외부 데이터 API를 호출하기 전에:
1. 잔액이 충분한지 확인해줘 (최소 10 USDC 필요)
2. 잔액이 충분하면 merchant_data_api 에 9.99달러 결제해줘
3. 결제 완료되면 결제 ID를 알려줘
```

## 직접 실행 (개발용)

```bash
# stdio 모드로 직접 실행
ROSUD_API_KEY=rosud_live_xxx rosud-mcp

# 또는 Python 모듈로 실행
ROSUD_API_KEY=rosud_live_xxx python -m rosud_mcp.server
```

## 테스트 실행

```bash
cd packages/mcp
pip install -e ".[dev]"
pytest tests/ -v
```

## 아키텍처

```
Claude Desktop
     │ MCP Protocol (stdio)
     ▼
rosud_mcp.server   ← MCP Server (app)
     │ tool 호출
     ▼
rosud_mcp.tools    ← 도구 정의 + 핸들러
     │ HTTP 요청
     ▼
rosud_mcp.client   ← httpx AsyncClient
     │ X-API-Key 인증
     ▼
Rosud Payment API  ← FastAPI (apps/api)
     │
     ▼
Circle USDC API    ← Base L2 블록체인
```

## 보안 주의사항

- API Key를 코드에 하드코딩하지 마세요. 항상 환경변수를 사용하세요.
- 결제는 되돌릴 수 없습니다. 금액과 수신자 주소를 반드시 확인하세요.
- `idempotency_key`를 사용하면 네트워크 오류 시 안전하게 재시도할 수 있습니다.
