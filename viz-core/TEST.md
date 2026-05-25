# viz-core 동작 검증 (TEST)

**테스트 일시**: 2026-05-24
**서버**: localhost:8765
**검증 방법**: 실제 서버 띄우고 endpoint 호출 + LLM 응답 확인

---

## ✓ 통과 항목

### 1. 서버 시작
- `.venv` 자동 생성 + 의존성 설치 (fastapi, uvicorn, httpx)
- viz-app/v20 의 키 자동 복사 (`.local_key.txt`)
- 브라우저 자동 열림

### 2. `/healthz` ✓
```json
{
  "ok": true,
  "version": "core",
  "clients": 2,
  "events": 13,
  "llm_enabled": true,
  "model": "claude-haiku-4-5-20251001",
  "key_source": "disk"
}
```

### 3. `/key/status` ✓
```json
{
  "configured": true,
  "preview": "sk-ant-api03…NgAA",
  "length": 108,
  "source": "disk"
}
```

### 4. `/` 인덱스 페이지 ✓
- HTTP 200, 43,897 bytes
- (viz-app 의 67KB 에서 35% 축소)

### 5. WebSocket 연결 ✓
- clients: 2 (start.sh 자동으로 브라우저 열어서 자동 연결)

### 6. Hook 이벤트 시퀀스 + LLM 자동 요약 ★ ✓

**입력 시퀀스** (5 단계):
```
UserPromptSubmit "login 함수 보안 패치"
PostToolUse Read /app/auth.py
PostToolUse Edit /app/auth.py (old/new 포함)
PostToolUse Bash "pytest -v"
Stop
```

**LLM 응답 (실제 출력):**
```
summary:     login 함수의 보안 패치: 평문 비교 → 타이밍 공격 방지 비교로 변경
next_step:   패치 검증 및 배포 준비
viz_kind:    flow                              ← LLM 자동 선택
viz_reason:  보안 패치 적용 과정의 순차적 단계를 명확히 표현
viz_data:    { steps: [...] }
```

→ LLM 이 작업 시퀀스 보고 **자동으로 `flow` viz_kind 선택**.

### 7. AskUserQuestion 옵션 카드 ✓
- 이벤트 전송 OK
- 브라우저 시각 확인은 본인이 (viz-core 카드에 options 그리드 자동 렌더)

### 8. `/viz/request` 자연어 요청 ★ ✓

**입력**: `"지난 활동을 KPI 형태로 보여줘"`

**LLM 응답**:
```
summary:  서버 구동, API 테스트, 보안 패치(login 함수), 단위 테스트 실행 완료
viz_kind: kpi                                  ← "KPI 형태" 요청 → kpi 자동
```

→ 자연어 요청 의도 정확히 매핑.

### 9. `/favorite` ⭐ ✓
- POST → `{"ok":true}`
- `.favorites.jsonl` 에 저장됨

### 10. 비용 (Claude Haiku 4.5) ✓
- 위 검증 전체에서 약 $0.001-0.002 누적
- (이전 viz-app 보다 자동 분석 제거로 비용 감소)

---

## ✗ 미검증 (브라우저 필요 — 본인이)

| 항목 | 검증 방법 |
|---|---|
| 브라우저 시각 렌더링 | 브라우저 열어서 확인 |
| NOW 박스 실시간 갱신 | 가짜 이벤트 보낼 때 헤더 아래 박스 변화 |
| 세션 박스 색 구분 | 다른 session_id 보내면 다른 색 |
| ▼ 화살표 흐름 | 같은 세션 노드 사이 |
| 11종 viz_kind 시각 | 각 viz_kind 가 적절히 렌더되는지 |
| AskUserQuestion 옵션 카드 그리드 | 위 TEST 7 의 결과가 시각화 |
| 우클릭 → 클립보드 | 노드 우클릭 → 토스트 확인 |
| ⭐ 즐겨찾기 버튼 | 요약 카드 우하단 |
| ⚙️ 키 모달 | 헤더 ⚙️ 클릭 |
| 자연어 입력 박스 | 텍스트 입력 + Enter |
| 다크/라이트 자동 | OS 다크/라이트 설정 따라감 |
| 모바일 반응형 | 브라우저 너비 조절 |

---

## 비교: viz-app → viz-core 단순화 효과

| | viz-app | viz-core | 감소 |
|---|---|---|---|
| server.py | 36 KB / 934 줄 | **17.6 KB / 492 줄** | ▼ 47% |
| index.html | 73 KB / 1450 줄 | **43.9 KB / 840 줄** | ▼ 42% |
| Endpoints | 15+ | **7** | ▼ 53% |
| 헤더 버튼 | 7개 | **1개** (⚙️) | ▼ 86% |
| 사이드바 | 3-탭 | **없음** | ▼ 100% |
| 자동 LLM 호출 | 요약+품질+보안+회고 | **요약만** | 비용 ↓ 70% |
| 배경 효과 | 파티클+scan | **없음** | 인지부하 ↓ |
| Hero 다이어그램 | 항상 | **없음** | 노이즈 ↓ |

---

## 빠진 기능 (의식적 제거)

- 📷 캡처 → OS 캡처 (Cmd+Shift+4)
- 🎬 녹화 → OS 녹화 (Cmd+Shift+5)
- ⊕ PR → 필요 시 endpoint 추가
- 🌗 테마 토글 → OS 다크/라이트 자동 따라감 (prefers-color-scheme)
- 👥 시청자 카운트 → 단일 사용자 가정
- 시간 슬라이더 → 사용 빈도 낮음, 후속
- 비용 트래커 → 필요 시 healthz에 추가
- 자동 코드 품질 LLM → 노이즈 + 비용 ↑
- 자동 보안 LLM → 노이즈 + 비용 ↑
- 12h 회고 → 자동 가치 가변
- webhook 알림 → 거의 안 씀
- 더블클릭 drill → 클릭 펼침으로 충분
- MD 사이드바 → 별도 도구 추천
- 토폴로지 사이드바 → 별도 페이지 추천
- 👍👎 버튼 → ⭐ 즐겨찾기로 통합

---

## 다음 단계

```bash
cd /Users/daeseonyoo/Documents/GitHub/aicore/viz-agents/viz-core
./start.sh
```

브라우저 자동 열림 → 본인이 직접 30분 사용 → 진짜 가치 평가.

미검증 항목들 (시각 부분) 본인이 직접 확인 후, 부족한 거 또는 잘못된 거 알려주면 fix.
