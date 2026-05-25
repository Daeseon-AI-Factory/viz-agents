# VIZ V5 — Code Deep Visualization

V4 base + LLM 프롬프트에 "코드의 의미론적 변화" 강조 추가.

## V4 → V5 변경

- `server.py` SUMMARY_SYSTEM 에 "함수/import/시그니처 변화 의미" 분류 강조
- LLM 이 코드 diff 를 단순 패치 X, "이게 보안 수정인지 / 리팩터링인지 / 기능 추가인지" 라벨링

## 한계 (V5 의도 vs 현재 구현)

- 진짜 AST 차원 분석은 아직 X — LLM 텍스트 추론만
- tree-sitter 같은 본격 파서 통합은 V5.x 후속
- 자세한 명세: `../viz-v5.md` 참고

## 실행
```bash
./start.sh
```
