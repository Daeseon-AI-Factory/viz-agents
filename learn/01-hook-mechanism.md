# 01. Hook 메커니즘 (어떻게 자동으로 잡히나)

> **이걸 모르면 "왜 자동으로 카드가 떠?" 이해 못함.**

---

## 한 줄

> Claude Code는 도구 쓸 때마다 본인 컴퓨터의 **shell 명령**을 실행할 수 있다. 그 shell 명령으로 viz-core에 POST 보냄.

---

## 어디 박혀있나

```bash
~/.claude/settings.json
```

이 파일 안 `hooks` 섹션에 등록.

---

## 실제 박힌 내용 (단순화)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "cat | curl -s --max-time 1 -X POST -H 'Content-Type: application/json' --data-binary @- http://localhost:8765/event >/dev/null 2>&1 || true # VIZ_V0_HUD"
          }
        ]
      }
    ]
  }
}
```

해석:
- **PostToolUse** = Claude가 도구 (Read/Edit/Bash 등) 다 쓴 직후
- **matcher: ".*"** = 모든 도구
- **command** = shell에서 실행할 명령
  - `cat | curl ... @-` = stdin (hook이 JSON 줌) 받아서 POST

---

## 시각화

```
Claude Code
   │
   │ Read api.py 도구 호출
   │
   ▼
도구 실행 끝
   │
   │ Claude Code 가 hook 발동
   │ stdin에 JSON 던짐:
   │ { "hook_event_name": "PostToolUse",
   │   "tool_name": "Read",
   │   "tool_input": {"file_path": "api.py"} }
   │
   ▼
shell command 실행
  cat (stdin 받기)
   │
   │ pipe
   ▼
  curl POST http://localhost:8765/event
   │
   ▼
viz-core 서버
```

---

## 잡히는 모든 이벤트 종류

| 이벤트 | 언제 |
|---|---|
| `UserPromptSubmit` | 사용자가 메시지 보냄 |
| `PreToolUse` | 도구 호출 직전 |
| **`PostToolUse`** | 도구 호출 직후 (★ 가장 중요) |
| `Stop` | Claude 응답 끝 |
| `SubagentStop` | 서브에이전트 끝 |
| `Notification` | Claude 가 사용자 입력 대기 |
| `SessionStart` | 세션 시작 |

---

## 왜 모든 Claude Code 세션이 같이 잡히나

```
~/.claude/settings.json 은 단 하나 (글로벌).
   ↓
어느 Claude Code 든 (어느 폴더든, 어느 클라이언트든) 같은 settings 읽음.
   ↓
즉 hook 도 같음.
   ↓
모든 세션의 모든 도구 호출 → 같은 localhost:8765/event 로.
   ↓
서버가 session_id 별로 박스 분리해서 보여줌.
```

---

## 설치 / 제거

```bash
# 설치
viz-core/install_hooks.py
   ↓
~/.claude/settings.json 에 위 명령 박음 (백업 후)
태그 # VIZ_V0_HUD 로 idempotent (중복 방지)

# 제거
viz-core/uninstall_hooks.py
   ↓
태그 들어간 라인만 제거 (다른 hooks 보존)
```

---

## 위험 / 주의

- **모든 도구 호출 → 외부 명령 실행** → 본인 머신 안에서만 안전. 외부 서버로 보내면 위험.
- **localhost:8765 만 사용** = 본인 머신 외부엔 안 나감.
- 만약 서버 죽었으면? → `|| true` 로 hook 실패해도 Claude Code 안 멈춤. `--max-time 1` 로 1초 안에 timeout.

---

## 핵심 이해 체크

본인이 이해해야 할 것:
- [ ] Hook = Claude Code 가 외부 shell 명령 실행하는 메커니즘
- [ ] settings.json 한 곳에 박혀있어서 모든 세션에 적용
- [ ] PostToolUse 가 가장 많이 잡힘
- [ ] hook 명령이 빠르게 안 끝나면 Claude Code 느려질 수도 → `--max-time 1` + 백그라운드

다음: [02-viz-kinds.md](./02-viz-kinds.md)
