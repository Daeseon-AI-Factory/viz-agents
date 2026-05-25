# VIZ V20 — Self-Learning Viz

V4 base + 사용자 피드백으로 시각 품질 학습.

## V4 → V20 변경

- 각 viz 카드에 👍 👎 버튼
- `server.py` 에 `POST /feedback` endpoint — `.feedback.jsonl` 에 저장
- LLM 호출 시 과거 피드백 context 일부 포함 (few-shot)

## 한계

- few-shot 학습만 (진짜 fine-tuning X)
- 피드백 데이터 양 적으면 효과 미미
- vector DB 유사도 검색 미구현
- 자세한 명세: `../viz-v20.md`

## 실행
```bash
./start.sh
```
