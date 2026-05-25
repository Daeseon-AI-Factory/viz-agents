# VIZ Live HUD — V18: Export & Share

**[← v17](./viz-v17.md)** · **[Roadmap](./viz-roadmap.md)** · **[v19 →](./viz-v19.md)**

---

## V18 — 내보내기 & 공유

### Upgrade from V17
V0~V17 = HUD 안에서 보기.
V18 = **시각을 밖으로** — 이미지/비디오/HTML/링크로 내보내고 공유.

### Why
- 동료한테 "이거 봐" 보내기
- 트위터/블로그 공유
- 문서/슬라이드에 임베드
- 회고 자료로 보관

### Exit criteria
- 현재 화면 PNG/SVG 캡처
- 시각 + 데이터 함께 JSON 내보내기
- 시간축 비디오 (10초 ~ 1분 녹화)
- 공유 링크 (만료 시간 설정)
- 임베드 코드 (iframe)

### 구체 시각화 예시

```
┌─ 시각 우클릭 메뉴 ──────────┐
│ 📷 PNG 캡처                  │
│ 🎬 10초 비디오 녹화           │
│ 🔗 공유 링크 (24시간 유효)    │
│ 📋 임베드 코드 복사            │
│ 📥 JSON 데이터 다운로드        │
└──────────────────────────────┘
```

### Architecture
- 캡처: html2canvas, dom-to-image
- 비디오: MediaRecorder API
- 공유 링크: 서버에서 임시 토큰 생성 → URL
- 임베드: iframe + 권한 토큰

### Dependencies
- frontend: html2canvas, ffmpeg.js (선택)
- 백엔드: 공유 토큰 저장 (Redis 같은 캐시)

### Risk
- 보안 (민감 데이터가 캡처에 포함 가능)
- 비디오 파일 크기 큼
- 공유 링크 누출

### 본인 비전 적합도
- ★★ — 핵심 X, 가치 전파에 중요

---

**다음:** [viz-v19.md](./viz-v19.md)
