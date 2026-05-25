# 03. LLM 호출 + 비용

> **이걸 모르면 "왜 갑자기 비용 청구가?" 당황한다.**

---

## 어떤 LLM 쓰나

```
모델: Claude Haiku 4.5 (claude-haiku-4-5-20251001)
제공: Anthropic API
호출: HTTPS POST → https://api.anthropic.com/v1/messages
인증: x-api-key 헤더 (sk-ant-...)
```

**왜 Haiku?** = 빠르고 싸기 때문 (Opus, Sonnet 보다).

---

## 가격 (2026-05 기준)

| | $/M tokens |
|---|---|
| 입력 (input) | $0.25 |
| 출력 (output) | $1.25 |

(1M = 1,000,000 토큰)

---

## 1회 호출 비용 계산

활동 요약 1건:
- 입력: 작업 시퀀스 (대략 600 토큰)
- 출력: JSON 응답 (대략 200 토큰)
- 비용 = (600 × $0.25 + 200 × $1.25) / 1,000,000
- ≈ **$0.0004** (한 번에 0.04센트)

---

## 언제 호출되나

| 트리거 | 비용 |
|---|---|
| Stop 이벤트 (1 turn 끝) | 1회 (요약) |
| 30 이벤트 누적 (긴 작업) | 1회 (강제 요약) |
| 60초 periodic 체크 | 0회 (조건 안 맞으면) |
| 자연어 요청 (`/viz/request`) | 1회 |
| (제거됨) 자동 코드 품질 분석 | viz-core에서는 안 함 |
| (제거됨) 자동 보안 체크 | 안 함 |

→ **일반적으로 매 turn 마다 1회**.

---

## 일/월 비용 추정

```
하루 작업량 추정 (본인 페르소나 기준):
  - Claude Code 30-60 turn / 일
  - 각 turn LLM 요약 = 1회
  - 30-60 × $0.0004 = $0.012 - $0.024 / 일
  
한 달:
  $0.36 - $0.72 / 월
  
즉 한 달에 천원 안팎.
```

자연어 요청 더 쓰면:
- 추가 1-5건 / 일 = 추가 $0.002

---

## 호출 안 됨 (LLM OFF)

키 없으면 (`ANTHROPIC_API_KEY` 미설정):
- LLM 호출 X
- 대신 **규칙 기반 fallback**:
  ```
  summary: "5× Read, 3× Edit, 2× Bash"
  viz_kind: "none"
  viz_data: {}
  ```
- 비용 $0

---

## 진짜 호출 코드 (단순화)

```python
async def _call_llm_summary(compact):
    key = await _get_key()  # 디스크에서 키 로드
    if not key:
        return _rule_based_summary(...)  # fallback
    
    user_msg = "다음 작업들을 분석:\n" + json.dumps(compact)
    
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 800,
                "system": SUMMARY_SYSTEM,  # viz_kind 가이드 포함
                "messages": [{"role": "user", "content": user_msg}],
            },
        )
    
    # 응답 파싱
    text = resp.json()["content"][0]["text"]
    return json.loads(text)  # {summary, viz_kind, viz_data, ...}
```

---

## 시스템 프롬프트 (LLM 에 매번 보냄)

```
당신은 AI 어시스턴트의 작업 시퀀스를 한국어로 분석합니다.
출력은 다음 JSON 형식만:
{
  "summary": "...",
  "viz_kind": "diff|table|gauge|flow|...",
  "viz_data": { ... }
}

viz_kind 가이드:
  - diff: 코드 변경 ...
  - gauge: 단일 수치 ...
  - ...
```

→ 이게 매 호출마다 input 으로 들어감 (캐싱 안 함). 입력 토큰 큰 이유.

---

## 비용 줄이는 법

1. **자동 분석 끄기** (이미 viz-core 에서 제거함 — 코드 품질/보안 자동)
2. **MIN_EVENTS_FOR_SUMMARY 늘리기** (4 → 10) → 작은 작업 요약 안 함
3. **자연어 요청 자제** — 진짜 필요할 때만
4. **LLM OFF 모드** (키 안 박음) — 비용 0, fallback 사용

---

## 다른 LLM 쓰려면

지금은 Anthropic 만. 다른 모델 쓰려면 server.py 의 `_call_llm_summary` 함수 안 endpoint URL + 응답 파싱만 바꿈.

후보:
- OpenAI: `https://api.openai.com/v1/chat/completions`
- Google: Gemini API
- 로컬: Ollama (무료)

---

## 핵심 이해 체크

- [ ] Claude Haiku 4.5 사용. 빠르고 싸다.
- [ ] 1회 호출 ≈ $0.0004 (0.04센트)
- [ ] 매 Stop 이벤트마다 1회 호출
- [ ] 한 달 비용 = 천원 안팎
- [ ] 키 없으면 fallback 모드 (비용 0)
- [ ] 다른 LLM 도 가능 (코드 수정)

다음: [04-ast-analysis.md](./04-ast-analysis.md)
