# 00. 전체 시스템 흐름 (한 페이지)

> **5분 안에 viz-core 의 동작 원리 전부 이해.**

---

## 한 그림

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Claude Code 사용 중                                        │
│  (브라우저 / VS Code / 터미널)                                │
│         │                                                  │
│         │ 1. 도구 사용 (Read, Edit, Bash 등)                 │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │  Hook 발동    │  ← ~/.claude/settings.json에 박혀있음     │
│  └──────┬───────┘                                          │
│         │ 2. cat + curl POST (JSON)                        │
│         ▼                                                  │
│  ┌─────────────────────────────────┐                       │
│  │  viz-core server (localhost:8765) │                     │
│  │                                  │                      │
│  │  ① /event 받음                    │                     │
│  │  ② session_events에 누적           │                     │
│  │  ③ Stop 도착 시 LLM 호출           │ ← Anthropic API     │
│  │  ④ LLM이 viz_kind+viz_data 선택   │   ($0.0005/회)      │
│  │  ⑤ WebSocket으로 broadcast       │                      │
│  └────────────┬─────────────────────┘                      │
│               │                                            │
│               │ 3. 실시간 push (WebSocket)                  │
│               ▼                                            │
│  ┌──────────────────────────────────┐                      │
│  │  브라우저 (localhost:8765)         │                     │
│  │                                  │                      │
│  │  ⑥ viz_kind 보고 적합 렌더러 호출  │                     │
│  │  ⑦ SVG/HTML 시각 컴포넌트 그림    │                      │
│  └──────────────┬───────────────────┘                      │
│                 │ 4. 사용자가 봄                            │
│                 ▼                                          │
│            ┌─────────┐                                     │
│            │  사용자   │  ← 0.5초 글랜스로 이해              │
│            └─────────┘                                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 4단계 요약

1. **Hook 발동** — Claude Code 가 도구 쓸 때마다 자동
2. **서버 받기 + LLM 분석** — 어떻게 보여줄지 결정
3. **브라우저 push** — WebSocket 실시간 전송
4. **시각 렌더** — viz_kind 별 컴포넌트 자동

---

## 각 단계 자세히 읽기

| 단계 | 자세한 문서 |
|---|---|
| Hook 작동 원리 | [01-hook-mechanism.md](./01-hook-mechanism.md) |
| 11종 viz_kind | [02-viz-kinds.md](./02-viz-kinds.md) |
| LLM 호출 + 비용 | [03-llm-call.md](./03-llm-call.md) |
| Python AST 분석 | [04-ast-analysis.md](./04-ast-analysis.md) |
| WebSocket 실시간 | [05-websocket.md](./05-websocket.md) |
| 데이터 흐름 상세 | [06-data-flow.md](./06-data-flow.md) |
| 비용 breakdown | [07-cost-breakdown.md](./07-cost-breakdown.md) |
| 실패/디버깅 | [08-failure-modes.md](./08-failure-modes.md) |

---

## 핵심 원리 한 줄

> **"Claude Code 가 무엇을 하든 자동으로 잡혀서 LLM 이 적합한 시각으로 그려준다."**

이거 이해하면 viz-core 전부 이해.
