# VIZ V10 — Real Animation Engine ★

**본인 비전 단어 "애니메이션처럼" 직격.**

V4 base + 진짜 움직이는 SVG/CSS 애니메이션.

## V4 → V10 변경

- `index.html` 에 `renderVizAnimation()` — SVG path 따라 점이 흐름
- LLM 프롬프트에 viz_kind `"animation"` 추가
- viz_data 형식: `{"nodes": [...], "edges": [{from, to}], "particles": [{path_id, duration_ms}]}`

## 시각화 예시

```
[API] ●────→ [Service] ────→ [DB]
      ↑ 점이 시간 흐름 따라 이동
```

CSS keyframes + SVG `<animateMotion>` 사용.

## 한계

- 복잡한 애니메이션 (Three.js, Lottie) 미구현 — 단순 SVG path 만
- 모바일 성능 영향 가능
- 자세한 명세: `../viz-v10.md`

## 실행
```bash
./start.sh
```
