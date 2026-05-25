# VIZ Live HUD — V17: Mobile Adaptive

**[← v16](./viz-v16.md)** · **[Roadmap](./viz-roadmap.md)** · **[v18 →](./viz-v18.md)**

---

## V17 — 모바일 적응

### Upgrade from V16
V0~V16 = 데스크탑 브라우저.
V17 = **모바일/태블릿** 화면 적응. 본인이 휴대폰에서 작업 상황 모니터링.

### Why
- 본인 자리 비울 때 휴대폰에서 Claude 작업 진척 확인
- 미팅 중 옆에서 살짝 확인
- 가벼운 푸시 알림 ("Claude 응답 완료", "에러 발생")

### Exit criteria
- 반응형 레이아웃 (320px ~ 1920px+)
- 터치 인터랙션 (drill-down, scroll)
- 모바일 푸시 (선택)
- 모바일-특화 NOW 박스 (한 줄로 압축)
- 오프라인 캐시 (네트워크 약할 때)

### 구체 시각화 예시 (모바일)

```
┌─ HUD (모바일) ─┐
│ ● 작업 중       │
│ ⚡ pytest       │
│ tests/test_api  │
├────────────────┤
│ 최근 5분 요약   │
│ api.py 2곳 수정 │
│ + tests 검증    │
├────────────────┤
│ [세션 1 →]      │
│ [세션 2 →]      │
│ [더 보기]       │
└────────────────┘
```

### Architecture
- CSS media queries
- viewport meta tag
- 터치 제스처 (swipe, pinch)
- PWA (선택, 홈 스크린에 설치)
- Service Worker (캐시)

### Dependencies
- CSS 적응
- PWA manifest
- Service Worker (선택)

### Risk
- 작은 화면에서 복잡한 시각 (V6, V8, V14)이 잘 안 맞음
- 터치 vs 마우스 인터랙션 차이
- 모바일 브라우저 호환성

### 본인 비전 적합도
- ★★ — 핵심 비전과 직접 연결 X, 편의성/접근성 향상

---

**다음:** [viz-v18.md](./viz-v18.md)
