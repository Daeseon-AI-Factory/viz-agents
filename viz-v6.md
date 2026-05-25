# VIZ Live HUD — V6: System Topology Live Map

**[← v5](./viz-v5.md)** · **[Roadmap](./viz-roadmap.md)** · **[v7 →](./viz-v7.md)**

---

## V6 — 시스템 토폴로지 라이브 맵

### Upgrade from V5
V5 = 한 파일/함수 단위의 코드 변화.
V6 = **전체 시스템**의 노드(서비스/모듈) + 연결 관계를 라이브 맵으로.

### Why (본인 비전 매핑)
> "시스템 시각화" — Claude가 어느 서비스/모듈을 만지는지, 어디서 어디로 데이터가 흐르는지 한눈에.

### Exit criteria
- 프로젝트의 모듈 그래프 자동 발견 (Python imports, JS imports, etc.)
- Claude가 만지는 노드에 실시간 펄스
- 서비스 간 호출 발생 시 노드 간 데이터 흐름 애니메이션
- 줌인/줌아웃 (큰 그림 → 디테일)

### 구체 시각화 예시

```
┌─ 시스템 맵 ────────────────────────────────────┐
│                                                │
│    [API Gateway] ──→ [Auth] ──→ [DB]           │
│         ▼   (펄스)                              │
│    [Cache]    ←── [Worker]                     │
│         │           ▲                          │
│         └─→ [Queue] ┘                          │
│                                                │
│  ⚡ Claude가 지금 만지는 노드: Auth (펄스)       │
│  ━━ 빨강 = 에러 발생  파랑 = 정상              │
└────────────────────────────────────────────────┘
```

### Architecture
- 서버: 프로젝트 루트 스캔 → import/dependency graph 생성
- Hook 시 → 만진 파일/모듈 노드에 highlight
- 클라이언트: D3 또는 React Flow로 그래프 렌더
- 노드 위치는 force-directed 자동 배치

### Tech
- 그래프 라이브러리: D3.js (force layout) 또는 cytoscape.js
- 프로젝트 스캔: 시작 시 cwd의 .py/.js/.ts 파일 import 추출
- 라이브 업데이트: WebSocket 으로 노드 펄스 트리거

### Dependencies
- frontend: D3.js (CDN) 또는 cytoscape.js
- backend: AST 기반 import 추출 (V0의 build_call_graph 재활용)

### Risk
- 큰 프로젝트는 노드 수백~수천 → 시각 압도
- 줌/필터링 UX 복잡
- 초기 스캔 시간 (1000+ 파일 = 10초+)

### V0~V3 와의 차이
- V0~V3 = 작업 이력 (시간축)
- V6 = 시스템 구조 (공간축) + 그 위에 실시간 활동 overlay

### V8 (Architecture Map) 과의 차이
- V6 = 코드 모듈 단위 (마이크로)
- V8 = 컴포넌트/배포 단위 (매크로)

---

**다음:** [viz-v7.md](./viz-v7.md)
