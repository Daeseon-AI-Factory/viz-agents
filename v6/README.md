# VIZ V6 — System Topology Live Map

V4 base + 시스템 모듈 그래프 사이드 패널.

## V4 → V6 변경

- `server.py` 에 `GET /topology` endpoint 추가 (cwd Python import 그래프)
- `index.html` 우측에 작은 토폴로지 패널 (D3 mini-graph 또는 텍스트 트리)
- 만지는 파일의 모듈에 펄스

## 한계

- D3 풀 force-directed graph는 V6.x 후속 (현재는 텍스트 트리 + 펄스)
- Python 만 — JS/Go 등은 후속
- 큰 프로젝트는 노드 압도 (필터링 추가 필요)
- 자세한 명세: `../viz-v6.md`

## 실행
```bash
./start.sh
```
