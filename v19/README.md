# VIZ V19 — Time-Travel Scrub

V4 base + 과거 시점 재생.

## V4 → V19 변경

- `server.py` 에 `GET /history?from=&to=` endpoint — 시간 범위 이벤트 조회
- `index.html` 헤더에 시간 슬라이더
- 슬라이더 이동 → 그 시점의 카드/시각 rerender

## 한계

- 이벤트 영구 저장은 메모리 500개 (디스크 DB 미구현 — V19.x 후속)
- 시간 슬라이더 UX 단순 (정밀 조작 어려움)
- 자세한 명세: `../viz-v19.md`

## 실행
```bash
./start.sh
```
