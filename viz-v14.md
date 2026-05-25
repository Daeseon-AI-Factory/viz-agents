# VIZ Live HUD — V14: Multi-Pane Layout

**[← v13](./viz-v13.md)** · **[Roadmap](./viz-roadmap.md)** · **[v15 →](./viz-v15.md)**

---

## V14 — 멀티 페인 레이아웃

### Upgrade from V13
V0~V13 = 단일 화면, 단일 시각.
V14 = **화면 분할**. 여러 시각 동시 비교/관찰.

### Why
사용자가 한 화면에 여러 정보 동시 봐야 할 때:
- 코드 변경 + 비즈니스 임팩트 동시
- 시스템 맵 + 카드 timeline 동시
- 두 세션 비교 (before/after)

### Exit criteria
- 드래그로 페인 분할
- 각 페인이 독립적인 시각 모드 (timeline / system map / KPI 등)
- 페인 크기 조절
- 레이아웃 저장/불러오기

### 구체 시각화 예시

```
┌─ 좌 페인 ──┬─ 우상 페인 ────┐
│ 시스템     │ NOW + 활동요약  │
│ 토폴로지    │                │
│ (V6 그래프)│                │
│            ├─ 우하 페인 ────┤
│            │ KPI 대시보드    │
│            │ (V9)           │
└────────────┴────────────────┘
```

### Architecture
- 클라이언트: split-pane 라이브러리 (또는 CSS grid)
- 각 페인이 같은 WebSocket 구독
- 페인별 시각 컴포넌트 인스턴스 분리

### Tech
- split.js 또는 react-split-pane
- 또는 vanilla CSS grid + drag

### Risk
- 작은 화면(모바일) 어려움 → V17 에서 별도 대응
- 각 페인이 너무 좁으면 의미 없음
- UX 복잡도 증가

### V12 (drill-down) 와의 관계
- V12 = 한 시각 안에서 깊이
- V14 = 여러 시각 동시
- 둘이 합쳐지면 = 본격 dashboard UI

---

**다음:** [viz-v15.md](./viz-v15.md)
