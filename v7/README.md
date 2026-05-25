# VIZ V7 — User Journey Visualization

V4 base + 사용자 여정 시각 컴포넌트 (가로 플로우).

## V4 → V7 변경

- `server.py` 에 `GET /routes` endpoint — FastAPI/Flask 라우터 자동 추출
- LLM 프롬프트에 "사용자 여정 어느 단계인지" 분류 강조
- viz_kind `journey` 추가 (V4 flow 확장)

## 한계

- 라우터 추출은 Python 만 (FastAPI/Flask 패턴 인식)
- 사용자 여정은 본질적으로 추측 — LLM 의존
- 백엔드만 있는 프로젝트는 가치 제한적
- 자세한 명세: `../viz-v7.md`

## 실행
```bash
./start.sh
```
