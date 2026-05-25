# VIZ V11 — What-If Simulator

V4 base + 변경 영향 시뮬레이션 컴포넌트.

## V4 → V11 변경

- `server.py` 에 `POST /whatif` endpoint — LLM 이 변경 → 영향 예측
- viz_kind `whatif` 추가 — 현재 vs 변경 후 side-by-side 비교

## 한계

- 시뮬레이션 정확도는 LLM 추측
- 외부 메트릭 데이터 없으면 단순 추측
- 자세한 명세: `../viz-v11.md`

## 실행
```bash
./start.sh
```
