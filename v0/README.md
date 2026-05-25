# VIZ V0 — Claude Code Live HUD

브라우저에서 Claude Code 작업을 **실시간으로 시각화**하는 V0.

## 무엇인가

```
┌─ Tab A ──────────────┐   ┌─ Tab B (이 V0) ───────────────────┐
│ Claude Code 터미널   │   │  ● 작업 중                          │
│                      │   │  💬 사용자 메시지                    │
│ > 이거 고쳐줘         │   │  📖 Read   src/api.py              │
│                      │   │  🔍 Grep   "TODO"                   │
│                      │   │  ✏️ Edit   src/api.py              │
│                      │   │  ⚡ Bash   pytest                   │
│                      │   │  ✓ 응답 완료                        │
└──────────────────────┘   └─────────────────────────────────────┘
```

채팅창 텍스트 안 읽고 옆 탭만 봐도 무슨 일 벌어지는지 보입니다.

## 설치 & 실행

```bash
./start.sh
```

처음 한 번:
- `.venv/` 자동 생성, FastAPI/uvicorn 설치
- `~/.claude/settings.json` 에 hooks 자동 등록 (백업 후)
- 브라우저가 자동으로 `http://localhost:8765` 열림

**Claude Code 세션을 재시작해야 hooks가 적용됩니다.**

## 동작 방식

```
Claude Code
   │ (tool 호출, 메시지 송수신마다)
   ▼ hook 실행
curl POST http://localhost:8765/event
   │
   ▼
FastAPI 서버 (server.py)
   │ WebSocket broadcast
   ▼
브라우저 (index.html) ─ 실시간 카드 추가
```

## 수신하는 이벤트

| 이벤트 | 카드 |
|---|---|
| UserPromptSubmit | 💬 사용자 메시지 |
| PostToolUse (Read) | 📖 Read [file] |
| PostToolUse (Edit/Write) | ✏️ Edit [file] |
| PostToolUse (Bash) | ⚡ Bash [command] |
| PostToolUse (Grep/Glob) | 🔍 검색 |
| PostToolUse (Agent/Task) | 🤖 Agent |
| PostToolUse (WebFetch/Search) | 🌐 웹 |
| PostToolUse (AskUserQuestion) | ❓ 질문 |
| Stop | ✓ 응답 완료 |
| SubagentStop | 🤖✓ 서브에이전트 종료 |
| Notification | 🔔 입력 대기 |

각 카드 클릭하면 JSON 원본 펼쳐짐.

## 종료

```bash
# 서버 종료
Ctrl+C

# hooks 제거 (Claude Code 다시 깨끗하게)
.venv/bin/python uninstall_hooks.py
```

## 파일

```
v0/
├── server.py            FastAPI + WebSocket. 80줄.
├── index.html           카드 타임라인 UI. 단일 파일.
├── install_hooks.py     ~/.claude/settings.json 에 hook 등록 (idempotent)
├── uninstall_hooks.py   hook 제거 (다른 hook은 보존)
├── start.sh             원커맨드 실행
└── README.md            이 파일
```

## 알려진 한계 (V0)

- hooks는 Claude Code 세션을 새로 시작해야 적용 — 핫리로드 불가
- 이벤트 순서는 도착 순. 동시 발생 시 약간 어긋날 수 있음
- 카드 형식만 지원 (V1에서 그래프/파일트리 추가 예정)
- 비용·토큰 정보는 hook 페이로드에 없어서 표시 안 함 (V2+)

## 다음 단계 (V1 후보)

- 파일 트리 사이드패널 — 읽힌 파일 하이라이트
- 액션 간 연결선 (이 Read → 이 Edit 으로 이어졌다)
- 서브에이전트 nested 카드
- 다크/라이트 토글
