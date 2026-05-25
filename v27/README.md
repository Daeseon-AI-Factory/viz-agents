# VIZ V27 — Anthropic Cost Tracker

V20 base + LLM 호출마다 토큰 사용량 누적 → 비용 표시.

## V20 → V27 변경
- 응답의 `usage` 필드에서 in/out 토큰 추출
- 헤더에 누적 비용 ($0.xx) 표시
- 일/주/월 통계 endpoint
