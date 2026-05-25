# VIZ V8 — Architecture Layer Map

V4 base + 인프라/배포 레이어 도식.

## V4 → V8 변경

- `server.py` 에 `GET /arch` endpoint — docker-compose, k8s yaml 파싱
- 레이어 분류 (Frontend / API / Service / Data / Infra) LLM 추론
- viz_kind `arch_layers` 추가 — 레이어별 박스 + 화살표

## 한계

- 메타 파일 없으면 추측 어려움
- 클라우드 (AWS/GCP) terraform 파싱 미구현
- 자세한 명세: `../viz-v8.md`

## 실행
```bash
./start.sh
```
