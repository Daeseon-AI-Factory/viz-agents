# VIZ Live HUD — V16: Collaboration

**[← v15](./viz-v15.md)** · **[Roadmap](./viz-roadmap.md)** · **[v17 →](./viz-v17.md)**

---

## V16 — 협업 (다중 사용자)

### Upgrade from V15
V0~V15 = 본인 머신, 본인만.
V16 = **여러 사람 같은 HUD 공유**. 페어 디버깅, 팀 작업 시각 공유.

### Why
- 토론토에서 동료와 페어 작업
- 원격 팀과 같은 시각 공유
- 상사한테 "지금 뭐 하고 있나" 보여주기

### Exit criteria
- HUD URL 공유 (실시간 sync)
- 다른 사람 마우스/포인터 보임
- 채팅 (또는 음성)
- 권한 (보기/편집)

### 구체 시각화 예시

```
┌─ 공유 HUD: viz.local/share/abc123 ──────────┐
│  현재 보고있는 사람:                          │
│  ● 김다선 (host)  ● Sarah (viewer)          │
│                                              │
│  [같은 시각, 둘 다 봄]                       │
│  Sarah 의 마우스 ↗ (실시간)                  │
│                                              │
│  ── 채팅 ──                                  │
│  Sarah: 이 함수 왜 이렇게?                   │
│  나: 보안 수정. 타이밍 공격 방어             │
└──────────────────────────────────────────────┘
```

### Architecture
- 호스트가 share URL 생성 → 시청자가 join
- WebSocket 으로 sync
- 또는 WebRTC peer-to-peer
- 백엔드: 세션 관리

### Dependencies
- WebSocket 확장
- 또는 third-party (Liveblocks, Yjs)

### Risk
- 보안 (누가 무엇을 볼 수 있나)
- 네트워크 의존도 증가
- 복잡한 sync 로직

### 본인 비전 적합도
- ★★★ — 본인 비전과 직접 연결은 아니지만, 토론토 팀 작업에서 가치 큼.

---

**다음:** [viz-v17.md](./viz-v17.md)
