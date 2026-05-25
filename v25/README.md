# VIZ V25 — Live Code Quality Score

V20 base + Edit 이벤트마다 LLM이 1-10 코드 품질 평가.

## V20 → V25 변경
- 매 Edit 후 LLM 호출 → "이 변경 품질 1-10"
- 헤더에 평균 점수 표시 + 색 indicator

## 한계
- LLM 호출 빈도 ↑ → 비용 ↑
- 평가 주관적 (LLM 의존)
