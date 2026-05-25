# VIZ V15 — On-Demand Viz Generation

V4 base + 사용자가 자연어로 시각 요청.

## V4 → V15 변경

- `index.html` 헤더 또는 사이드에 자연어 입력 박스
- `server.py` 에 `POST /viz/request` — 자연어 → LLM → viz 명세 → 렌더

## 한계

- LLM 응답 시간 (3-5초 대기)
- 모호한 요청은 빈약한 시각
- 과거 데이터 (timeline 검색) 제한적
- 자세한 명세: `../viz-v15.md`

## 실행
```bash
./start.sh
```
