# VIZ V13 — Multi-Agent Integration

V4 base + 다른 AI 에이전트 출력 통합.

## V4 → V13 변경

- `server.py` 가 `agent_id` 필드 처리 (event POST 에 포함 시)
- `index.html` 헤더에 에이전트 칩 + 색 매핑
- 같은 hook endpoint 에 다른 에이전트 (SI/QA/OPS) 도 POST 가능

## 한계

- 다른 에이전트 (SI/QA/OPS) 자체가 아직 빌드 안 됨 → 시뮬레이션만 가능
- 표준 hook protocol 합의 필요 — 현재는 ad-hoc
- 자세한 명세: `../viz-v13.md`

## 실행
```bash
./start.sh
```
