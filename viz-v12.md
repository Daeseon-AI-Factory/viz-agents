# VIZ Live HUD — V12: Interactive Drill-Down

**[← v11](./viz-v11.md)** · **[Roadmap](./viz-roadmap.md)** · **[v13 →](./viz-v13.md)**

---

## V12 — 인터랙티브 드릴다운

### Upgrade from V11
V0~V11 = 보기만 (passive).
V12 = **사용자가 클릭/탐색** (active). 시각 위에서 깊이 들어감.

### Why (본인 비전 매핑)
> 본인이 비-엔지니어 = 깊이가 필요할 때 코드 안 보고 GUI 로 들어가야 함.

### Exit criteria
- 모든 시각 노드 클릭 가능 (drill down)
- 클릭 → 그 안에 더 자세한 시각
- 호버 → 툴팁
- 멀티 레벨 (3-5 단계 깊이)
- Breadcrumb 으로 돌아가기

### 구체 인터랙션

```
1단계 (시스템 맵):
  [API] [Service] [DB]
        ↓ click on [Service]
2단계 (서비스 안):
  [Auth] [Payment] [Notification]
        ↓ click on [Auth]
3단계 (모듈 안):
  [login_handler] [verify_token] [refresh]
        ↓ click on [login_handler]
4단계 (함수 안):
  코드 + 호출 흐름 + 최근 트래픽
```

### Architecture
- 클라이언트: 클릭 이벤트 → 새 시각 fetch/render
- 서버: 노드별 상세 데이터 endpoint
- LLM 도움: 사용자가 보는 레벨에 맞는 요약

### Tech
- React/Vue/Svelte (또는 vanilla JS) 상태 관리
- 시각 컴포넌트가 nested 가능
- transition (zoom in/out) 애니메이션

### Risk
- 너무 깊이 들어가면 길 잃음 (네비게이션 어려움)
- 각 레벨에 적절한 데이터 준비 필요
- 모바일 인터랙션 어려움

### V10 와의 관계
V10 (애니메이션) + V12 (인터랙션) = 풀 모션 그래픽 + 직접 조작 = Apple Keynote 급 시각.

---

**다음:** [viz-v13.md](./viz-v13.md)
