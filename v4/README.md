# VIZ V4 — LLM-Driven Dynamic Visualization

V3 + 작업 디스크립션에 따라 LLM이 시각화 종류를 자동 선택해서 다른 컴포넌트 렌더.

## V3 → V4 변경점

V3 = 카드 timeline (모든 작업 같은 시각).
V4 = 작업마다 다른 시각화. LLM이 분류 + 데이터 결정.

### 작동 흐름

```
의미 있는 작업 (4 events+) 누적
       ↓
서버: LLM 호출 → JSON 응답
  {
    "summary": "한국어 요약",
    "next_step": "...",
    "files_touched": [...],
    "viz_kind": "diff | gauge | table | flow | badge | code | none",
    "viz_data": { 컴포넌트별 데이터 }
  }
       ↓
브라우저: viz_kind 보고 적절한 렌더러 호출
       ↓
요약 카드 안에 시각화 컴포넌트 자동 펼침
```

## 지원 viz_kind 컴포넌트

| viz_kind | 언제 | 시각 |
|---|---|---|
| `diff` | 코드/텍스트 변경 (Edit/Write) | 좌(빨강 -) / 우(초록 +) 패널 |
| `gauge` | 단일 수치 변화 (테스트 통과율 등) | 큰 숫자 + 진행 바 |
| `table` | 여러 항목 나열 (검색 결과) | 데이터 표 |
| `flow` | 순서 있는 단계 (배포) | 단계 카드 + 화살표 |
| `badge` | 단일 상태 (성공/실패) | 색 알약 |
| `code` | 짧은 코드 스니펫 | 코드 박스 |
| `none` | 시각화 불필요 | 표시 X |

## V4 단계 (a→b→c→d) 통합

| 단계 | 무엇 | V4 안에서 |
|---|---|---|
| V4a | LLM 메타 분류 | server.py SUMMARY_SYSTEM 안에 박힘 |
| V4b | diff 컴포넌트 | renderVizDiff() |
| V4c | gauge/table/flow/badge/code | 다른 renderViz* 함수들 |
| V4d | LLM 자유 HTML | (V5 또는 V4.1 — 보안 sanitize 작업 필요. 현재 V4d는 미구현) |

## 실행

```bash
cd v4
./start.sh
```

V3의 키 자동 복사. 처음이면 ⚙️ 키 설정 모달에서 입력.

## 검증 (V4 가치 있나)

1. 같은 도구(Edit) 라도 작업 내용에 따라 다른 viz_kind 나옴?
2. 빨강/초록 diff가 즉시 이해되나? (텍스트 안 읽고)
3. 작업 종류 다양해질수록 시각 다양해지나?

## V4 한계 (V5+ 후보)

- **V4d (LLM 자유 HTML/SVG) 미구현** — XSS sanitize 필요. 별도 작업.
- viz_kind 분류 정확도가 LLM 의존
- 사전 정의 컴포넌트 7개에 제한됨 (LLM이 새 시각 못 만듦)
- 코드 의미론적 시각 (V5) 아직 없음 — 단순 diff만
- 시스템 토폴로지 (V6) 없음
- 진짜 애니메이션 (V10) 없음

→ V5~V20 로드맵은 `viz-roadmap.md` 참고.
