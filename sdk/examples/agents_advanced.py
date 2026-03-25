"""
에이전트 관리 심화 예시 - Rosud Python SDK

AI 에이전트의 지갑과 권한을 세밀하게 관리하는 패턴:
- 에이전트 생성 시 지출 한도 & 화이트리스트 설정
- 에이전트 활성화/비활성화 전략
- 멀티 에이전트 마켓플레이스 패턴
- 에이전트별 지출 추적 & 리포트
"""
import os
from typing import Optional

import rosud
from rosud.exceptions import InsufficientFundsError, PaymentError, RosudError


# ──────────────────────────────────────────────────────────
# 1. 에이전트 생성 패턴
# ──────────────────────────────────────────────────────────

def create_task_agent(
    client: rosud.Rosud,
    name: str,
    daily_limit: float,
    per_tx_limit: float,
    allowed_recipients: Optional[list[str]] = None,
) -> Optional[str]:
    """
    특정 작업 전용 에이전트 생성.

    에이전트 = 독립적인 USDC 지갑을 가진 AI 서브계정
    - 일일 지출 한도로 예산 초과 방지
    - 건당 한도로 실수/오용 방지
    - 화이트리스트로 허가된 수신자에게만 지급 가능
    """
    try:
        agent = client.agents.create(
            name=name,
            spending_limit_daily=daily_limit,
            spending_limit_per_tx=per_tx_limit,
            allowed_recipients=allowed_recipients or [],
        )

        print(f"✅ 에이전트 생성: {agent.name}")
        print(f"   ID: {agent.id}")
        print(f"   일 한도: {agent.spending_limit_daily} USDC")
        print(f"   건당 한도: {agent.spending_limit_per_tx} USDC")
        if agent.allowed_recipients:
            print(f"   허용 수신자: {len(agent.allowed_recipients)}개")

        if hasattr(agent, "api_key"):
            print(f"   API 키: {agent.api_key}")
            print(f"   ⚠️  이 키를 안전하게 보관하세요. 다시 조회 불가능!")
            return agent.api_key

        return None

    except RosudError as e:
        print(f"❌ 에이전트 생성 실패: {e.message}")
        return None


def setup_multi_agent_system(client: rosud.Rosud) -> None:
    """
    멀티 에이전트 시스템 구성 예시.

    역할 분리:
    - 리서치 에이전트: 정보 수집 API 호출
    - 실행 에이전트: 서비스 구매 및 결제
    - 감사 에이전트: 지출 모니터링 (읽기 전용)
    """
    print("=== 멀티 에이전트 시스템 구성 ===\n")

    # 리서치 에이전트 — 저렴한 API 호출 전용
    research_agent_key = create_task_agent(
        client,
        name="ResearchAgent-v1",
        daily_limit=10.00,         # 일 10 USDC
        per_tx_limit=0.50,         # 건당 최대 0.50 USDC (API 호출비)
        allowed_recipients=[
            "0xDataProviderAPI",
            "0xSearchServiceAPI",
        ],
    )

    print()

    # 실행 에이전트 — 서비스 구매 담당
    execution_agent_key = create_task_agent(
        client,
        name="ExecutionAgent-v1",
        daily_limit=100.00,        # 일 100 USDC
        per_tx_limit=25.00,        # 건당 최대 25 USDC
        allowed_recipients=[
            "0xServiceProviderA",
            "0xServiceProviderB",
            "0xComputeProvider",
        ],
    )

    print("\n🔧 에이전트 시스템 구성 완료")
    print("   각 에이전트 API 키를 해당 서비스에 환경변수로 주입하세요:")
    print("   ROSUD_API_KEY=<에이전트_API_키>")


# ──────────────────────────────────────────────────────────
# 2. 에이전트 목록 조회 & 지출 리포트
# ──────────────────────────────────────────────────────────

def agent_spending_report(client: rosud.Rosud) -> None:
    """에이전트별 지출 현황 리포트"""
    try:
        agents = client.agents.list(limit=20)
        print(f"=== 에이전트 지출 리포트 ({agents.total}개 에이전트) ===\n")

        total_spent = 0.0
        for agent in agents:
            status = "🟢" if agent.is_active else "🔴"

            # 에이전트의 최근 결제 조회 (에이전트 API 키 있을 때)
            print(f"{status} {agent.name}")
            print(f"   ID: {agent.id}")
            print(f"   일 한도: {agent.spending_limit_daily or '무제한'} USDC")
            print(f"   건당 한도: {agent.spending_limit_per_tx or '무제한'} USDC")
            print(f"   등록일: {agent.created_at:%Y-%m-%d}")
            print()

    except RosudError as e:
        print(f"에이전트 조회 실패: {e.message}")


# ──────────────────────────────────────────────────────────
# 3. 에이전트-to-에이전트 결제 패턴 (A2A)
# ──────────────────────────────────────────────────────────

def agent_to_agent_payment_example() -> None:
    """
    에이전트 간 직접 결제 패턴 (A2A).

    시나리오: "오케스트레이터" 에이전트가 작업을 완료한
    "워커" 에이전트에게 자동으로 보상 지급.

    각 에이전트는 별도 API 키로 독립 인증.
    """
    print("=== A2A (에이전트-to-에이전트) 결제 ===\n")

    # 워커 에이전트 지갑 주소 (미리 파악해야 함)
    WORKER_AGENT_WALLET = os.environ.get("WORKER_WALLET", "0xWorkerAgentWallet")

    # 오케스트레이터 에이전트 클라이언트
    orchestrator = rosud.Rosud(
        api_key=os.environ.get("ORCHESTRATOR_API_KEY", "rosud_live_orchestrator_xxx")
    )

    try:
        # 워커 에이전트 잔액 확인
        balance = orchestrator.wallets.get_balance()
        print(f"오케스트레이터 잔액: {balance.amount} USDC")

        if float(balance.amount) >= 0.10:
            # 작업 완료 보상 지급
            payment = orchestrator.payments.create(
                amount=0.10,
                to=WORKER_AGENT_WALLET,
                memo="task_completion_reward:analyze_data_v1",
                idempotency_key="reward-task-001-v1",  # 중복 지급 방지
            )
            print(f"✅ 워커 에이전트 보상 지급 완료")
            print(f"   결제 ID: {payment.id}")
            print(f"   금액: {payment.amount} USDC")
            print(f"   상태: {payment.status}")
        else:
            print(f"⚠️  잔액 부족 ({balance.amount} USDC < 0.10 USDC)")

    except InsufficientFundsError:
        print("❌ 오케스트레이터 잔액 부족. USDC를 충전하세요.")
    except PaymentError as e:
        print(f"❌ 결제 실패 [{e.error_code}]: {e.message}")
    finally:
        orchestrator.close()


# ──────────────────────────────────────────────────────────
# 4. 에이전트 비활성화 & 정리 패턴
# ──────────────────────────────────────────────────────────

def cleanup_inactive_agents(client: rosud.Rosud, dry_run: bool = True) -> None:
    """
    오래된 / 비활성 에이전트 정리.

    dry_run=True이면 삭제 목록만 출력 (기본값 — 안전)
    dry_run=False이면 실제 삭제 수행
    """
    try:
        agents = client.agents.list(limit=100)
        inactive = [a for a in agents if not a.is_active]

        print(f"비활성 에이전트: {len(inactive)}개 (전체 {agents.total}개)\n")

        for agent in inactive:
            print(f"  {'[DRY RUN] ' if dry_run else ''}삭제 예정: {agent.name} ({agent.id})")
            print(f"    등록일: {agent.created_at:%Y-%m-%d}")

            if not dry_run:
                client.agents.delete(str(agent.id))
                print(f"    ✅ 삭제 완료")

        if dry_run and inactive:
            print(f"\n실제 삭제하려면 dry_run=False로 실행하세요.")

    except RosudError as e:
        print(f"오류: {e.message}")


# ──────────────────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = rosud.Rosud(
        api_key=os.environ.get("ROSUD_API_KEY", "rosud_live_your_key_here")
    )

    print("=== 에이전트 관리 심화 예시 ===\n")

    print("1. 멀티 에이전트 시스템 구성")
    print("-" * 40)
    setup_multi_agent_system(client)

    print("\n2. 에이전트 현황 리포트")
    print("-" * 40)
    agent_spending_report(client)

    print("\n3. A2A 결제 패턴")
    print("-" * 40)
    agent_to_agent_payment_example()

    print("\n4. 비활성 에이전트 정리 (dry run)")
    print("-" * 40)
    cleanup_inactive_agents(client, dry_run=True)

    client.close()
