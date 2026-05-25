# VIZ Live HUD — V8: Architecture Layer Map

**[← v7](./viz-v7.md)** · **[Roadmap](./viz-roadmap.md)** · **[v9 →](./viz-v9.md)**

---

## V8 — 아키텍처 레이어 맵

### Upgrade from V7
V7 = 사용자 여정.
V8 = **시스템 아키텍처 전체 도식**. 레이어/컴포넌트/배포 + 트래픽 오버레이.

### Why (본인 비전 매핑)
> "아키텍처 시각화" — Claude가 만지는 게 어느 레이어 (DB/서비스/API/CDN/...)인지, 그 변경이 어디까지 영향 미치는지.

### Exit criteria
- 레이어 다이어그램: Frontend / API / Service / Data / Infra
- 각 컴포넌트의 배포 위치 (region, container, 등)
- 컴포넌트 간 트래픽/의존성 화살표
- Claude의 변경이 어느 레이어 영향인지 강조

### 구체 시각화 예시

```
┌─ 아키텍처 ─────────────────────────────────────┐
│                                                │
│  ▓ Frontend Layer                              │
│    [Next.js (Vercel)] ←── (CDN: Cloudflare)   │
│                ↓ HTTPS                         │
│  ▓ API Layer                                   │
│    [FastAPI (ECS)] ←── ⚡ Claude 여기 수정     │
│                ↓ ↑                             │
│  ▓ Service Layer                               │
│    [Auth] [Payment] [Notification]             │
│         ↓                                      │
│  ▓ Data Layer                                  │
│    [PostgreSQL (RDS)] [Redis (ElastiCache)]   │
│                                                │
└────────────────────────────────────────────────┘
```

### Architecture
- 프로젝트 메타 파일 (docker-compose, k8s, serverless.yml, terraform) 파싱
- 레이어 자동 분류 (LLM 도움)
- 클라이언트: 박스+화살표 + 레이어 헤더

### Dependencies
- 메타 파서: docker-compose, k8s yaml, terraform .tf
- LLM: 컴포넌트 → 레이어 분류
- frontend: 박스 레이아웃 (그리드)

### Risk
- 메타 파일 없으면 추측 어려움
- 클라우드/온프레미스 차이
- 큰 아키텍처는 시각 복잡

### V6 와의 차이
- V6 = 코드 모듈 (코드 내부)
- V8 = 배포/컴포넌트 (인프라 위)

### V13 (Multi-Agent Integration) 과의 관계
- V8이 인프라 도식이면, V13은 그 위에 다른 AI 에이전트(SI/QA/OPS)가 어느 컴포넌트에 작용하는지 오버레이

---

**다음:** [viz-v9.md](./viz-v9.md)
