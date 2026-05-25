# 07. 비용 breakdown (어떻게 돈 나가나)

> **방심하면 한 달에 만원 넘게 나갈 수도. 알고 써야.**

---

## 한 줄

> 거의 모든 비용 = **Anthropic API LLM 호출**. 나머지는 0.

---

## 비용 매트릭스

| 기능 | LLM 호출 | 빈도 | 1회 비용 | 일 비용 (60 turn 가정) |
|---|---|---|---|---|
| **활동 요약** (Stop마다) | ✓ Haiku | 매 turn | $0.0004 | **$0.024** |
| **자연어 시각 요청** | ✓ Haiku | 사용자 의도 | $0.0006 | $0.003 (5건) |
| 코드 분석 (📦) | ✗ AST 만 | 사용자 의도 | $0 | $0 |
| Hook 이벤트 수신 | ✗ | 매 도구 호출 | $0 | $0 |
| WebSocket 브로드캐스트 | ✗ | 매 이벤트 | $0 | $0 |
| viz_kind 렌더링 | ✗ 브라우저 | 매 카드 | $0 | $0 |
| ⭐ 즐겨찾기 저장 | ✗ | 사용자 의도 | $0 | $0 |
| 키 저장/테스트 | ✗ | 가끔 | $0 | $0 |
| MD 파일 watcher | ✗ | 자동 | $0 | $0 |

**합계 (예상): 일 $0.027 / 월 $0.81 / 년 $9.86**

→ 한 달 천원 미만.

---

## 비용 폭발 케이스 (조심)

### Case A. 매번 자동 LLM 분석 (이전 viz-app)
```
PostToolUse Edit 마다:
  - 활동 요약 LLM (1회)
  - 자동 코드 품질 LLM (1회)  ← viz-core 에서 제거함
  - 자동 보안 체크 LLM (1회)  ← viz-core 에서 제거함
  
3배 비용 → 월 $2.4
```

### Case B. 큰 입력 (수천 토큰)
```
30 events 누적 시 한 번에 분석
  → 입력 토큰 5,000+
  → 1회 $0.003 (8배)
```

### Case C. 자연어 요청 남용
```
사용자가 매 분 자연어 요청
  → 60건/시간 × 8시간 = 480건/일
  → 480 × $0.0006 = $0.29/일 = $8.7/월
```

---

## 비용 모니터링

### 실시간 (viz-core 에서 제거)
viz-core 는 비용 트래커 UI 제거 (단순화). 필요하면 직접:

```bash
curl http://localhost:8765/healthz | grep usage
```

(현재 viz-core 의 healthz 에는 cost 없음. 추가하려면 server.py 수정.)

### Anthropic 대시보드
- https://console.anthropic.com/usage
- 실시간 사용량 + 비용 그래프 + 한도 설정

### 한도 설정 (강력 추천)
```
console.anthropic.com → Settings → Limits
  월 한도 = $5 또는 $10
  넘으면 자동 차단
```

→ 폭주해도 안전.

---

## 무료로 쓰는 법

### 1. LLM 끄기
키 안 박으면 → fallback 모드:
```
summary: "5× Read, 3× Edit, 2× Bash"
viz_kind: "none"
```
비용 $0. 하지만 요약 품질 ↓.

### 2. 로컬 LLM (Ollama)
```bash
# Ollama 깔기
brew install ollama
ollama pull llama3

# server.py 수정 — Anthropic API → Ollama
url: http://localhost:11434/api/chat
```
무료. 하지만 응답 품질 모델에 따라.

### 3. 다른 클라우드 LLM
- Groq (무료 tier 있음)
- Google Gemini (무료 한도)
- OpenAI gpt-4o-mini (비슷한 가격)

---

## 본인 페르소나에 맞는 권장

```
비-엔지니어 + 가벼운 사용:
  - 활동 요약만 (자연어 요청 가끔)
  - 월 비용: $0.5-2
  - Anthropic 한도: $5 설정
  
적극 활용:
  - 자연어 요청 + 코드 분석 + 즐겨찾기
  - 월 비용: $2-10
  - Anthropic 한도: $20 설정
```

---

## 핵심 이해 체크

- [ ] 비용 = LLM 호출만 ($0.0004/회)
- [ ] 매 Stop 이벤트마다 1회 호출
- [ ] 일반 사용 = 월 천원 안팎
- [ ] 자동 분석 (코드/보안) 켜면 비용 ↑
- [ ] Anthropic 대시보드에서 한도 설정 추천
- [ ] 무료 옵션: LLM 끄기 / Ollama 로컬

다음: [08-failure-modes.md](./08-failure-modes.md)
