# VIZ Build Report v3 — V5~V20 진짜 풀 빌드

**작업 시각**: 2026-05-24 새벽 (사용자 "끝까지 계속" 요청 후)
**이전 보고**: report-2 에서 V10만 깊었음, 나머지는 표면. **사용자 짜증 → 진짜 풀 빌드.**

---

## 한 줄

V5~V20 모든 버전에 **진짜 새 기능 코드** 추가. 더 이상 LLM 프롬프트만 다른 표면 X.

---

## 각 버전 진짜 추가된 것

| 버전 | 진짜 추가된 코드 |
|---|---|
| **V5** | `server.py` 에 `_extract_py_symbols()` + `_diff_py_symbols()` — Python 코드에서 함수/클래스/import 변화를 regex로 추출. Edit 이벤트에 symbol_diff 자동 포함. |
| **V6** | `server.py` 에 `GET /topology` endpoint (history 에서 만진 .py 파일 모아 import 그래프). `index.html` 에 우측 사이드 패널 + SVG 원형 노드 그래프 (5초마다 갱신). |
| **V7** | viz_kind `"journey"` + `renderVizJourney()` — 사용자 여정 가로 단계 (이탈% 표시). |
| **V8** | viz_kind `"arch"` + `renderVizArch()` — 아키텍처 레이어 박스 (Frontend/API/Service/Data + active highlight). |
| **V9** | viz_kind `"kpi"` + `renderVizKpi()` — 3-6개 KPI 카드 그리드 (값/추세/델타). |
| **V10** | ★ viz_kind `"animation"` + `renderVizAnimation()` — **SVG `<animateMotion>` 로 점이 노드 사이 흐르는 진짜 애니메이션**. 본인 비전 "애니메이션처럼" 직격. |
| **V11** | viz_kind `"whatif"` + `renderVizWhatif()` — 현재 vs 변경후 side-by-side + good/bad 컬러 + 추천 박스. |
| **V12** | 노드 **더블클릭** → 풀스크린 drill-down 모달 (raw JSON 펼침). `node._evData` 에 원본 박아둠. |
| **V13** | `AGENT_COLORS` 매핑 (claude/si/qa/ops/adr/doc/auto), `agent_id` 받아서 세션 박스에 에이전트 컬러/아이콘. |
| **V14** | `⊞ 페인` 토글 버튼 + `body.pane-2` 클래스 + 우측 `#side-pane` (events/sessions/summaries 통계 + viz_kind 분포). |
| **V15** | `POST /viz/request` endpoint + 헤더 아래 **자연어 입력 박스** ("지난 5분 활동을 KPI로 보여줘" 같은 요청 → LLM → 즉시 시각). |
| **V16** | `setInterval(refreshLlmBadge, 5000)` + 헤더에 `👥 N명 시청 중` 뱃지 (healthz 의 clients 카운트). |
| **V17** | CSS `@media (max-width: 768px)` + `(max-width: 480px)` — 모바일 적응 (단일 컬럼, 폰트 축소, 터치 영역 확대). |
| **V18** | html2canvas CDN 추가 + 헤더에 `📷` 캡처 버튼 → PNG 다운로드. |
| **V19** | `GET /history` endpoint + 헤더 아래 **시간축 슬라이더** (이동 시 그 시점 이후 카드 흐리게). |
| **V20** | `POST /feedback` + `GET /feedback` endpoints + `.feedback.jsonl` 저장 + 각 요약 카드에 **👍 👎 버튼** (클릭 → 서버 저장). |

---

## 21개 폴더 = 126개 파일

```
viz-agents/
├── viz-roadmap.md
├── viz-v4.md ~ viz-v20.md      (17개 spec)
├── viz-build-report.md         (V4 까지)
├── viz-build-report-2.md       (V5-V20 표면 — 이전 잘못된 보고)
├── viz-build-report-3.md       ← 지금 이 파일 (V5-V20 진짜 빌드)
├── v0/ ~ v20/                  (21 × 6 = 126 코드 파일)
└── CLAUDE.md, MEMORY.md
```

---

## 깨서 우선 확인할 버전 (본인 비전 직격순)

1. **V10** — `cd v10 && ./start.sh`. 실제 작업 시키면 LLM이 viz_kind=animation 선택 시 SVG 점이 노드 사이 흐르는 거 보임.
2. **V15** — `cd v15 && ./start.sh`. 헤더 아래 입력 박스에 "지난 활동 KPI로 보여줘" 같은 거 입력 → LLM이 즉시 시각 생성.
3. **V19** — `cd v19 && ./start.sh`. 헤더 아래 슬라이더 이동 → 과거 시점 카드만 보임.
4. **V20** — `cd v20 && ./start.sh`. 요약 카드 아래 👍👎 → `.feedback.jsonl` 에 저장됨.
5. **V18** — `cd v18 && ./start.sh`. 📷 버튼 → 현재 화면 PNG 캡처.
6. **V14** — `cd v14 && ./start.sh`. ⊞ 페인 → 우측 통계 패널.
7. **V13** — `cd v13 && ./start.sh`. hooks 가 agent_id 보내면 (현재는 claude만) 에이전트별 색.

---

## 솔직한 한계 (여전히)

1. **V6 토폴로지** — 단순 원형 배치 (D3 force-directed 아님). 의존성 큰 프로젝트는 압도.
2. **V11 What-If** — LLM 시뮬레이션이라 정확도 가변.
3. **V13 Multi-Agent** — 다른 AI 에이전트 (SI/QA/OPS) 자체가 빌드 안 됨. 시뮬레이션만 가능.
4. **V14 Multi-Pane** — split.js 같은 본격 drag-resize 없음. 토글 on/off 만.
5. **V16 Collab** — 같은 endpoint 다중 접속만 (시청자 카운트). 사용자별 커서/권한 X.
6. **V17 Mobile** — CSS 만. PWA / 푸시 X.
7. **V19 Time-Travel** — 메모리 500개 한정. 디스크 DB X.
8. **V20 Self-Learning** — feedback 저장만. LLM이 실제로 활용 X (V20.x 후속).

근데 각 버전 **진짜 동작하는 새 기능** 한 개씩은 있음. report-2 의 "표면적" 비판은 더 이상 해당 X.

---

## 사용한 패턴

대부분 V4 base 에 한 가지씩:
- viz_kind 새 종류 (`renderVizXxx`) — V7, V8, V9, V10, V11
- 새 endpoint (`/topology`, `/history`, `/feedback`, `/viz/request`) — V6, V15, V19, V20
- 새 UI 요소 (모달, 슬라이더, 입력박스, 버튼) — V12, V18, V19, V20
- 새 데이터 처리 (agent_id, symbol_diff) — V5, V13
- CSS 적응 — V17, V14

---

## 시간 / 비용

- 추가 작업: 약 1.5시간
- 추가 LLM 비용: $0
- 사용자가 본 메시지 한 개

---

## 다음 결정 (본인이 깨서)

```
선택지 A: 실제 마음에 드는 버전 1-2개 골라서 본인 페인 검증
선택지 B: 본인 비전 6영역 중 가장 필요한 거부터 검증
  (V5=코드, V6=시스템, V7=제품, V8=아키텍처, V9=비즈니스, V10=애니메이션)
선택지 C: 가장 마음에 든 버전 → 다음 차원 (V21+) 으로 확장
```

---

**잘 자요. 깨면 v10/start.sh 가장 먼저, 그 다음 v15/start.sh 시도.**
