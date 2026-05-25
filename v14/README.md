# VIZ V14 — Multi-Pane Layout

V4 base + 분할 화면.

## V4 → V14 변경

- `index.html` 에 split-pane (CSS grid + drag-resize)
- 각 페인 독립 뷰 선택 (timeline / system map / KPI)

## 한계

- 모바일 (V17) 에서는 자동으로 단일 페인 fallback
- 페인 레이아웃 저장/불러오기 미구현
- 자세한 명세: `../viz-v14.md`

## 실행
```bash
./start.sh
```
