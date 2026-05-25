# 06. 데이터 흐름 상세 (전체 trace)

> **하나의 도구 호출이 화면에 카드로 뜨기까지의 모든 단계.**

---

## 시나리오: Claude 가 Edit api.py 실행

### 단계별 trace

```
T+0ms    Claude Code 가 Edit tool 호출
         tool_input: {
           file_path: "/app/api.py",
           old_string: "return None",
           new_string: "return result"
         }
                ↓
T+1ms    Edit 실제 실행 (파일 수정)
                ↓
T+50ms   PostToolUse hook 발동
         stdin 에 JSON 전달:
         {
           "hook_event_name": "PostToolUse",
           "session_id": "abc12345",
           "tool_name": "Edit",
           "tool_input": { ... }
         }
                ↓
T+51ms   shell command 실행:
         cat | curl -s --max-time 1 -X POST \
              -H 'Content-Type: application/json' \
              --data-binary @- http://localhost:8765/event
                ↓
T+60ms   ┌────────────────────────────────────┐
         │  viz-core server: POST /event       │
         │                                    │
         │  1. raw body 읽음                   │
         │  2. JSON parse                      │
         │  3. record 만듦                     │
         │     { ts: "16:48:03",               │
         │       data: { hook_event_name,      │
         │              session_id, ... } }    │
         │  4. _history.append(record)         │
         │  5. await _broadcast(record)        │
         │     → _clients 안 모든 socket 에      │
         │       send_json(record)             │
         │  6. _session_events 에 누적          │
         │     (session_id 별)                 │
         │  7. Stop 이벤트면 _try_summarize    │
         │     백그라운드 태스크 (asyncio)      │
         └────────────────────────────────────┘
                ↓
T+62ms   브라우저 WebSocket onmessage:
         add(event)
                ↓
T+63ms   add() 안에서:
         - session_id 확인 (없으면 _orphan)
         - sessionFor(sid) 호출 — 색 매핑
         - makeNode(ev) — 노드 DOM 생성
         - getOrCreateSessionBox — 박스 있으면 재사용, 없으면 생성
         - appendNodeToSession — 박스 안에 노드 추가 + ▼
         - bumpBoxToTop — 활성 박스를 위로 이동
         - updateNow(ev) — NOW 박스 갱신
                ↓
T+65ms   화면에 ✏️ Edit /app/api.py 카드 보임
         + NOW 박스에 "✏️ 파일 수정 중" 표시
```

총 **65ms** = 사용자가 거의 즉시 봄.

---

## Stop 이벤트 (요약 생성)

```
Claude Code 응답 끝
         ↓
Stop event POST /event
         ↓
서버:
   - broadcast (Stop 카드 보임)
   - _try_summarize(sid, "stop") 백그라운드 시작
         ↓
   ┌────── 백그라운드 ──────┐
   │                       │
   │ _session_events 안의   │
   │ 이 session 이벤트 모음  │
   │         ↓             │
   │ _compact_events()      │
   │ (이벤트 압축, LLM 입력) │
   │         ↓             │
   │ _call_llm_summary()    │
   │ → Anthropic API 호출   │
   │   (1-3초)              │
   │         ↓             │
   │ LLM 응답:              │
   │ {summary, viz_kind,    │
   │  viz_data, ...}        │
   │         ↓             │
   │ record 생성:           │
   │ {hook_event_name:      │
   │   "_summary", ...}     │
   │         ↓             │
   │ _broadcast(record)     │
   │                       │
   └───────────────────────┘
         ↓
브라우저 onmessage:
   makeSummaryNode(ev) 호출
   → viz_kind 보고 적합 렌더러
   → 활동 요약 카드 + viz 컴포넌트
```

총 **2-5초** (LLM 응답 시간 포함).

---

## 자연어 시각 요청 (사용자가 직접)

```
사용자가 입력 박스에 "지난 활동 KPI" 입력
   ↓
브라우저: fetch("/viz/request", {request: "..."})
   ↓
서버 POST /viz/request:
   - 최근 30개 이벤트 가져옴
   - _compact_events 로 압축
   - LLM 호출 (시스템 프롬프트 + 사용자 요청)
   - 응답 parse
   - record 만듦 (session_id="_user_request")
   - _broadcast
   ↓
브라우저: WebSocket 으로 받음
   - makeSummaryNode → 카드 + viz 렌더
```

---

## 코드 분석 요청 (사용자가 파일 경로)

```
사용자가 📦 박스에 파일 경로 + 분석 클릭
   ↓
브라우저: fetch("/analyze/code", {path: "..."})
   ↓
서버 POST /analyze/code:
   - _analyze_python_file(path)  ← LLM 안 씀
     - ast.parse
     - 클래스/함수/import/calls 추출
   - _analyze_to_viz(analysis)
     - calls 가 많으면 viz_kind="callgraph"
     - viz_data 채움 (nodes, edges)
   - record 만듦
   - _broadcast
   ↓
브라우저: callgraph 렌더러
   - 계층 배치 (in_degree=0 → 왼쪽)
   - SVG 화살표 + 점 흐름
```

---

## 모든 데이터의 종류 (record.data 의 hook_event_name)

| 값 | 어디서 | 특별한 처리 |
|---|---|---|
| `UserPromptSubmit` | Claude Code hook | NOW 갱신 |
| `PreToolUse` | hook | 무시 (노이즈) |
| **`PostToolUse`** | hook | 카드 추가 |
| `Stop` | hook | LLM 요약 트리거 |
| `SubagentStop` | hook | 카드 |
| `Notification` | hook | 카드 (입력 대기) |
| **`_summary`** | 서버 자체 생성 | 활동 요약 카드 + viz |

`_` 시작 = 서버가 만든 메타 이벤트 (Claude 가 보낸 게 아님).

---

## 핵심 이해 체크

- [ ] Hook → POST → broadcast → 브라우저 (65ms)
- [ ] Stop 이벤트 → 백그라운드 LLM 호출 (2-5초)
- [ ] 자연어 요청 → 같은 LLM 경로
- [ ] 코드 분석 → LLM 없이 AST 만 (즉시)
- [ ] `_summary` 같은 메타 이벤트 = 서버가 만든 것

다음: [07-cost-breakdown.md](./07-cost-breakdown.md)
