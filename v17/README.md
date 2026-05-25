# VIZ V17 — Mobile Adaptive

V4 base + 모바일/태블릿 적응 CSS.

## V4 → V17 변경

- `index.html` CSS media queries 강화 (320px ~ 1920px+)
- 헤더/카드 모바일 압축 모드
- 터치 인터랙션 (tap 영역 확대)

## 한계

- 본격 PWA (Service Worker, 푸시) 미구현
- 복잡한 시각 (V6 topology, V14 multi-pane) 모바일에서 단순화
- 자세한 명세: `../viz-v17.md`

## 실행
```bash
./start.sh
```
모바일에서 `http://[Mac IP]:8765` 접속.
