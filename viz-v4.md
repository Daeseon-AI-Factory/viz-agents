# VIZ Live HUD — V4: LLM-Driven Dynamic Visualization

**[← Roadmap](./viz-roadmap.md)** · **[v5 →](./viz-v5.md)**

---

## V4 — LLM-Driven Dynamic Visualization

### Upgrade from V3
V0~V3 = 도구 활동을 카드/그래프 timeline 으로 정렬. **고정된 시각**.
V4 = LLM이 작업 디스크립션 보고 **그때그때 다른 시각을 생성**. 동적.

### Why
본인이 직접 말함:
> "시각화를 하나만 하는게 아니고 정말 AI가 하는 각 작업이 뭔지 그리고 실제 디스크립션에 따라서 시각화가 사람이 바로 알 수 있게해야지"

### Sub-versions (a → b → c → d)

#### V4a — LLM 메타 분류 (15분)
- 기존 `_summary` 응답에 `viz_kind` 1줄 추가
- LLM이 분류만: `"diff" | "table" | "gauge" | "flow" | "badge" | "code" | "none"`
- 클라는 분류를 카드 헤더에 표시 (시각 X)
- **검증**: 같은 도구도 작업마다 다른 분류 나오나? → 동적의 첫 신호

#### V4b — 첫 컴포넌트 렌더 (30분)
- 분류가 `"diff"` → Edit의 `old_string`/`new_string` 빨강/초록 패치 렌더
- 다른 분류는 카드만
- **검증**: 그 시각 보고 클릭 안 해도 즉시 이해되나?

#### V4c — 컴포넌트 추가 (30분)
- 분류가 `"gauge"` → 진행률/수치 미터
- 분류가 `"table"` → 데이터 표
- 분류가 `"flow"` → 단계 화살표 시각
- **검증**: 작업마다 다른 시각이 자동으로?

#### V4d — LLM 자유 명세 (1시간)
- 사전 컴포넌트 라이브러리 X
- LLM이 HTML/SVG/Mermaid 자유 생성
- 무한 동적
- **검증**: 본인 비전 풀 도달?

### Exit criteria
- 같은 도구(Edit) 라도 작업 내용에 따라 다른 시각이 자동으로 뜸
- 본인이 옆 창 보고 텍스트 안 읽고 무슨 일 일어났는지 즉시 파악
- V4 a~d 각각 후 본인 평가 가능

### Architecture

```
hook 이벤트 (Stop, 의미 있는 작업)
       ↓
서버: _try_summarize → LLM 호출
       ↓
LLM 입력: 이벤트 시퀀스 (compact)
LLM 출력: {
  "summary": "한국어 요약",
  "viz_kind": "diff|gauge|table|flow|badge|code|none",
  "viz_data": { 컴포넌트별 데이터 },
  "viz_html": "..." (V4d, 자유 생성)
}
       ↓
broadcast _summary 이벤트
       ↓
브라우저: viz_kind 보고 적절한 렌더러 호출
       ↓
화면에 작업별 다른 시각 출력
```

### LLM 프롬프트 (V4a)

```
시스템: 도구 호출 시퀀스를 받아서 한국어 요약 + 어떤 시각화 종류가 어울리는지 분류.

출력 JSON 형식:
{
  "summary": "...",
  "viz_kind": "diff|table|gauge|flow|badge|code|none",
  "viz_reason": "왜 그 종류 골랐는지 한 줄"
}

viz_kind 가이드:
- diff: 코드/텍스트 변경이 보일 때 (Edit/Write)
- table: 여러 항목 비교/나열 (search 결과, 데이터)
- gauge: 단일 수치 변화 (테스트 통과율, 응답시간)
- flow: 순서 있는 단계 (배포, 마이그레이션)
- badge: 단일 상태 (통과/실패, 활성/비활성)
- code: 코드 스니펫 표시
- none: 시각화 불필요 (단순 Read 등)
```

### Risk

- LLM이 viz_kind 잘못 분류 → fallback "none"
- LLM 출력 JSON 파싱 실패 → fallback 규칙 기반
- viz_data 빈약 → 빈 컴포넌트 안 보이게 (graceful)
- V4d (자유 HTML) → XSS 위험 — sanitize 필수

### 이후 (V5+) 와의 관계
V4 = **메커니즘** (LLM이 시각을 생성한다는 패턴 자체).
V5~V10 = 그 메커니즘 위에 각 비전 영역별 **특화 시각** 추가.

---

**다음:** [viz-v5.md](./viz-v5.md)
