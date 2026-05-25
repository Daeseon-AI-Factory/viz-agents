# VIZ Live HUD — V10: Real Animation Engine

**[← v9](./viz-v9.md)** · **[Roadmap](./viz-roadmap.md)** · **[v11 →](./viz-v11.md)**

---

## V10 — 진짜 애니메이션 엔진

### Upgrade from V9
V0~V9 = 정적 시각 (간단한 펄스/슬라이드 정도).
V10 = **진짜 움직이는 애니메이션**. 본인이 처음 비전 말할 때 정확히 쓴 단어 — "**애니메이션처럼**".

### Why (본인 비전 매핑)
> "애니메이션처럼 보여주고" — 본인 비전의 정수. 이게 진짜 도달하면 본인이 처음 그린 그림.

### Exit criteria
- 데이터 흐름이 화살표 따라 **점/입자**로 흘러감 (시간축에 움직임)
- 함수 호출 = 노드 → 노드 사이 펄스 이동
- 코드 diff = 빨강 줄 fade-out → 초록 줄 fade-in (Apple Keynote급)
- 시스템 부하 변화 = 노드 크기/색 부드러운 보간
- 사용자 액션 = 화면 시뮬레이션 (마우스 커서 자동 이동)

### 구체 시각화 예시

```
시각이 정적 X. 시간축 진행:

t=0: [API] ──→ [Service]
t=1: [API] ●─→ [Service]    ← 점이 움직임
t=2: [API] ──●→ [Service]
t=3: [API] ──→●[Service]
t=4: [API] ──→ [Service]●   ← 도착, 노드 펄스
t=5: [API] ──→ [Service]
              ↓
              [DB]
              ●  ← 새로운 점이 다음 단계로
```

### Architecture
- 클라이언트: CSS animations + JS requestAnimationFrame + SVG path 애니
- 또는 Lottie (After Effects 출력)
- 또는 WebGL/Three.js (3D 또는 고성능 2D)
- 서버: 이벤트만 보내고, 애니메이션은 클라이언트가 시간축에 매핑

### Tech 후보
- 가장 단순: CSS keyframes
- 중간: GSAP (GreenSock)
- 고급: Lottie / Three.js / Pixi.js

### Dependencies
- CSS animations (기본)
- GSAP CDN (선택)

### Risk
- 성능: 너무 많은 동시 애니메이션 = 브라우저 느림
- 과잉 자극: 항상 움직이면 피로
- 적절한 trigger 결정이 어려움 (언제 멈추나)

### V0~V9 와의 차이
- V0~V9 = 정적 상태 표시
- V10 = 변화의 **과정** 시각

### 이게 진짜 본인 비전 직격
> "코드, 시스템, 제품, 아키텍처, 비즈니스를 전부 시각화해서 **애니메이션처럼** 보여주고"
> ↑ 이 단어. V10이 도달점.

---

**다음:** [viz-v11.md](./viz-v11.md)
