# VIZ V9 — Business KPI Stream

V4 base + 비즈니스 KPI 카드 컴포넌트.

## V4 → V9 변경

- `server.py` 에 `GET /kpi` endpoint — mock KPI 데이터 (실제 외부 연동은 V9.x)
- viz_kind `kpi` 추가 — 4개 메트릭 카드 + 추세 화살표
- LLM 프롬프트에 "코드 변경 → 비즈니스 임팩트 추정" 추가

## 한계

- 외부 API (Stripe, GA, Mixpanel) 연동 미구현 — mock 데이터만
- 비즈니스 임팩트 추정은 본질적으로 부정확
- 자세한 명세: `../viz-v9.md`

## 실행
```bash
./start.sh
```
