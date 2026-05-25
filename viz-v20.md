# VIZ Live HUD — V20: Self-Learning Viz

**[← v19](./viz-v19.md)** · **[Roadmap](./viz-roadmap.md)**

---

## V20 — 자가 학습 시각

### Upgrade from V19
V0~V19 = LLM이 한 번에 시각 생성, 고정 품질.
V20 = **사용자 피드백**으로 LLM이 시각 품질을 점진 개선.

### Why
- LLM이 만든 시각이 항상 좋지는 않음
- 본인이 "이거 좋아 / 별로" 표시 → LLM이 학습
- 시간 지나면 본인 취향에 맞게 자동 조정

### Exit criteria
- 모든 시각에 👍 👎 버튼
- 피드백 저장 (시각 종류 + 컨텍스트 + 평가)
- LLM이 새 시각 생성 시 과거 피드백 참고
- "이 종류 시각 다 별로면 사용 안 함" 학습

### 구체 시각화 예시

```
┌─ 시각 ─────────────────┐
│  [diff 시각]            │
│                        │
│            👍 👎 [수정] │
└────────────────────────┘
       ↓ 본인이 👎 누름
       ↓
다음에 비슷한 작업:
LLM 이 "이 컨텍스트엔 diff 별로니 table 로" 자동 변경
```

### Architecture
- 피드백 DB: {viz_kind, context_features, feedback, timestamp}
- LLM 호출 시 context examples 같이 보냄 ("과거에 이런 컨텍스트 + 이런 시각엔 👍/👎")
- few-shot 학습 (prompt 안에 예시)
- 또는 진짜 fine-tuning (장기)

### Dependencies
- 피드백 DB (SQLite)
- LLM context window 활용
- 또는 vector DB (피드백 유사도 검색)

### Risk
- 피드백 양 적으면 학습 어려움
- 잘못된 피드백 (실수로 👎)
- 본인 취향이 일관되지 않을 수 있음

### V4 와의 관계
- V4 = LLM 한 번에 시각 생성
- V20 = 그 위에 사용자 피드백 학습 레이어

### 마지막 버전 = "완성"?
**아님.** V20도 표면. 본인 비전 ("계속 고도화") 따라 V21, V22, V30... 가능.

가능한 V21+ 후보:
- V21: 음성 인터페이스 ("Claude, 결제 흐름 보여줘")
- V22: AR/VR 시각 (Vision Pro 등)
- V23: 다른 LLM(GPT, Gemini 등) 통합
- V24: 자동 데모 생성 (스크린레코딩 + 시각 합성)
- V25: 본인 외 동료에게 자동 시각 알림
- ...

---

**[← Roadmap](./viz-roadmap.md)**
