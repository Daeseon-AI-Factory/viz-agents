# 08. 실패 케이스 & 디버깅

> **뭔가 안 되면 여기 먼저 보기.**

---

## 증상 → 원인 → 해결

### 1. 브라우저에서 아무것도 안 보임

| 원인 | 확인 | 해결 |
|---|---|---|
| 서버 안 뜸 | `curl http://localhost:8765/healthz` 응답? | `./start.sh` |
| Hook 안 박힘 | `cat ~/.claude/settings.json \| grep VIZ_V0_HUD` | `python install_hooks.py` |
| Claude Code 재시작 안 함 | 새 hook 적용은 새 세션부터 | Claude Code 새 세션 시작 |
| 브라우저 캐시 | 옛 페이지 | Cmd+Shift+R |

---

### 2. LLM 요약이 "활동 없음 (API 401)" 같이 뜸

| 원인 | 확인 | 해결 |
|---|---|---|
| 키 미설정 | healthz `llm_enabled` false | ⚙️ 키 모달에서 입력 |
| 키 오타 | 키가 sk-ant- 로 시작? | 다시 입력 |
| 키 폐기됨 | console.anthropic.com 확인 | 새 키 발급 |
| API 한도 초과 | console 사용량 확인 | 한도 늘리기 |
| 네트워크 끊김 | `curl https://api.anthropic.com` | wifi 확인 |
| 서버 재시작 안 함 | 키 바꿨는데 서버 옛 키 메모리 | server 재시작 |

---

### 3. 카드 떠도 viz_kind 가 항상 "none"

| 원인 | 해결 |
|---|---|
| LLM 이 시각화 부적합 판단 | 정상. 단순 read 등은 시각 X. |
| LLM 응답 JSON 파싱 실패 | log 확인: `/tmp/viz-core.log` |
| 시스템 프롬프트 부실 | server.py 의 SUMMARY_SYSTEM 수정 |

---

### 4. 노드 이름 잘림 / 화살표 안 보임 / 점 안 흐름

| 원인 | 해결 |
|---|---|
| renderVizCallgraph 에 데이터 부족 | nodes ≥ 2 + edges ≥ 1 필요 |
| 노드 너무 많아 폭 초과 | 자동 가로 늘림. 안 되면 scroll |
| SVG animateMotion 미지원 | 모던 브라우저 다 지원. Safari 14+ |

---

### 5. WebSocket 끊김 (헤더 "재연결…" 표시)

| 원인 | 해결 |
|---|---|
| 서버 죽음 | `./start.sh` |
| 서버 포트 바뀜 | 코드 확인 |
| 컴퓨터 sleep 후 깸 | 1.5초 자동 재연결 |

자동 재연결되니까 보통 가만히 두면 됨.

---

### 6. 매번 hook 발동에 Claude Code 느려짐

| 원인 | 해결 |
|---|---|
| 서버 응답 느림 | server.py log 확인 |
| `--max-time 1` 누락 | install_hooks.py 코드 확인 |

→ 정상이면 hook 자체는 50ms 이내.

---

### 7. 비용 폭주 ($/일 정상보다 10배)

| 원인 | 해결 |
|---|---|
| 자동 코드 품질 / 보안 분석 켜져있음 | viz-core 는 제거됨. 이전 viz-app/v25/v26 사용 중인지 확인 |
| 30 events 자주 누적 (큰 작업) | MIN_EVENTS_FOR_SUMMARY 늘리기 |
| 자연어 요청 남용 | 절제 |

---

### 8. 같은 카드가 두 번 뜸

| 원인 | 해결 |
|---|---|
| 브라우저 탭 2개 열림 | 한 탭 닫기 (broadcast 양쪽으로) — 정상 |
| Hook 중복 등록 | uninstall 후 reinstall |

---

### 9. settings.json 망가짐 (다른 hooks 도 잃음)

| 원인 | 해결 |
|---|---|
| install_hooks.py 오작동 | 백업 파일 있음: `~/.claude/settings.json.bak.YYYYMMDD_HHMMSS` |

```bash
cp ~/.claude/settings.json.bak.20260524_1648 ~/.claude/settings.json
```

---

### 10. 분석 한 파일이 텍스트 표 (table) 로만 보임

| 원인 | 해결 |
|---|---|
| 함수 간 호출 관계 없음 | 정상. 분석 결과 calls=0 이면 table 보임. |
| 클래스만 있음 | viz_kind="arch" 로 자동. |

---

## 로그 확인

```bash
# 서버 로그
tail -f /tmp/viz-core.log

# 또는 foreground 실행 — 모든 출력 즉시 보임
.venv/bin/python server.py
```

---

## 디버깅 명령 모음

```bash
# 서버 상태
curl -s http://localhost:8765/healthz | python3 -m json.tool

# 최근 이벤트
curl -s 'http://localhost:8765/history?limit=10' | python3 -m json.tool

# 키 상태
curl -s http://localhost:8765/key/status | python3 -m json.tool

# 직접 가짜 이벤트 (테스트)
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"hook_event_name":"PostToolUse","session_id":"test","tool_name":"Bash","tool_input":{"command":"ls"}}' \
  http://localhost:8765/event

# 코드 분석 직접
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"path":"/Users/daeseonyoo/.../server.py"}' \
  http://localhost:8765/analyze/code | python3 -m json.tool

# hook 등록 상태
grep -c "VIZ_V0_HUD" ~/.claude/settings.json
```

---

## 안 풀리는 경우

1. **서버 완전 종료 + 재시작**:
   ```bash
   lsof -ti :8765 | xargs kill
   ./start.sh
   ```

2. **hook 완전 제거 + 재설치**:
   ```bash
   python uninstall_hooks.py
   python install_hooks.py
   ```

3. **브라우저 캐시 완전 삭제** (시크릿 모드로 테스트)

4. **로그 보고 알려주기**:
   ```bash
   tail -50 /tmp/viz-core.log
   ```

---

## 핵심 이해 체크

- [ ] 90% 문제 = 서버 재시작으로 해결
- [ ] 키 문제 = healthz 의 llm_enabled 보기
- [ ] settings.json 망가지면 백업 있음
- [ ] 로그 = /tmp/viz-core.log
- [ ] 비용 폭주 = 자동 분석 켜진 거 의심
