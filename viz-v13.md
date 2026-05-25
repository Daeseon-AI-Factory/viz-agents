# VIZ Live HUD — V13: Multi-Agent Integration

**[← v12](./viz-v12.md)** · **[Roadmap](./viz-roadmap.md)** · **[v14 →](./viz-v14.md)**

---

## V13 — 다른 AI 에이전트 통합

### Upgrade from V12
V0~V12 = Claude Code 한 에이전트만.
V13 = **다른 AI 에이전트 (SI/QA/OPS/ADR/DOC/AUTO) 출력 통합** 하나의 HUD에.

### Why (본인 비전 매핑)
> ai-core 플랫폼 전체 비전: 8개 AI 직군 (SI/QA/OPS/VIZ/CORE/ADR/DOC/AUTO). VIZ는 그 모든 출력의 universal HUD가 되어야 함.

### Exit criteria
- SI(코드생성), QA(테스트), OPS(운영), ADR(결정), DOC(문서) 등 다른 서비스의 출력이 같은 HUD에 들어옴
- 에이전트별 색/태그 구분
- 에이전트 간 협업 시각 (SI가 만들고 QA가 검증 등)
- 통합 timeline + 통합 NOW

### 구체 시각화 예시

```
┌─ Multi-Agent HUD ──────────────────────────────────┐
│                                                    │
│  🔵 Claude (메인)   🟢 SI    🟡 QA    🟠 OPS       │
│                                                    │
│  지금:                                              │
│  🔵 사용자가 신기능 요청                            │
│  🟢 SI 가 코드 생성 중                              │
│  🟡 QA 가 새 테스트 작성 대기                       │
│                                                    │
│  ── 흐름 ──                                        │
│  사용자 → 🔵 → 🟢 → 🟡 → 🟠 → 배포                 │
│            완료 진행중 대기 미시작                   │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Architecture
- 각 AI 서비스가 같은 hook protocol (POST /event) 사용
- 또는 별도 endpoint per service (POST /event/si, /event/qa, ...)
- 서버: 모든 출력 통합, agent_id로 구분
- 클라이언트: 색/탭/필터로 분리

### Dependencies
- 다른 AI 서비스들이 hook을 emit 해야 함 (각 서비스 측 작업)
- ai-core 플랫폼의 표준 contract 활용

### Risk
- 다른 서비스가 아직 빌드 안 됨 → 시뮬레이션만
- 표준 hook protocol 합의 필요
- 통합 UX가 복잡해질 수 있음

### V0~V3 와의 차이
- V0~V3 = Claude Code 단일 세션
- V13 = 멀티 에이전트 멀티 세션

### ai-core platform 와의 관계
- 본인 큰 비전의 핵심: 8개 직군 통합 universal HUD
- VIZ V13 = 그 통합 UI

---

**다음:** [viz-v14.md](./viz-v14.md)
