# VIZ V26 — Live Security Check

V20 base + Edit 이벤트마다 LLM이 보안 취약점 체크.

## V20 → V26 변경
- 매 Edit 후 LLM 호출 → "보안 이슈 있나"
- 발견 시 ⚠️ 배지 + 빨강 강조
- SQL injection / XSS / 비밀 노출 / 위험 함수 사용 등

## 한계
- LLM이 모든 취약점 못 잡음 (정적 분석 도구 보완 필요)
- 비용 ↑
