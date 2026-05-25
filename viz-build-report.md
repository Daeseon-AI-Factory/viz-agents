# VIZ Build Report — 자는 동안 완료된 작업

**작업 시각**: 2026-05-23 (사용자 취침 후)
**완료된 산출물**: 23개 파일

---

## 한 줄 요약

V4~V20 풀 로드맵 (17개 spec 문서 + 1 로드맵) + **V4 실제 코드 빌드 완료**.
V5~V20 코드는 본인 평가 후 결정 — spec 만 있음.

---

## 산출물 1 : 로드맵 (1개)

| 파일 | 내용 |
|---|---|
| `viz-agents/viz-roadmap.md` | V4~V20 전체 그림 한 페이지 + 본인 비전 6영역 매핑 표 |

---

## 산출물 2 : 17개 버전별 spec 문서

`viz-agents/viz-v4.md` ~ `viz-agents/viz-v20.md`

| 버전 | 한 줄 |
|---|---|
| viz-v4.md  | LLM-Driven Dynamic Visualization — 작업마다 다른 시각 |
| viz-v5.md  | Code Deep Viz — AST 차원 코드 변화 |
| viz-v6.md  | System Topology Live Map — 모듈 그래프 + 라이브 펄스 |
| viz-v7.md  | User Journey Visualization — 제품 시각 |
| viz-v8.md  | Architecture Layer Map — 인프라 도식 |
| viz-v9.md  | Business KPI Stream — 비즈니스 시각 |
| viz-v10.md | **Real Animation Engine** — 진짜 애니메이션 ★ 본인 비전 단어 직격 |
| viz-v11.md | What-If Simulator — 적용 전 시뮬레이션 |
| viz-v12.md | Interactive Drill-Down — 클릭해서 깊이 |
| viz-v13.md | Multi-Agent Integration — 다른 AI 에이전트 통합 |
| viz-v14.md | Multi-Pane Layout — 분할 화면 |
| viz-v15.md | On-Demand Viz Generation — 자연어로 시각 요청 |
| viz-v16.md | Collaboration — 다중 사용자 |
| viz-v17.md | Mobile Adaptive — 모바일 |
| viz-v18.md | Export & Share — 캡처/공유 |
| viz-v19.md | Time-Travel Scrub — 과거 시점 재생 |
| viz-v20.md | Self-Learning Viz — 피드백 학습 |

---

## 산출물 3 : V4 실제 코드 (6개 파일)

`viz-agents/v4/`

| 파일 | 역할 |
|---|---|
| `server.py` | FastAPI + WebSocket + LLM 호출 with viz_kind 출력 |
| `index.html` | 동적 시각화 렌더러 7종 (diff/gauge/table/flow/badge/code/none) |
| `install_hooks.py` | 공용 hooks 설치 |
| `uninstall_hooks.py` | 공용 hooks 제거 |
| `start.sh` | V3 키 자동 복사 + 서버 시작 |
| `README.md` | V4 사용법 + 한계 |

---

## V4 핵심 메커니즘

```
1. Stop 이벤트 (4+ 작업 누적)
       ↓
2. 서버 → LLM 호출 (Claude Haiku 4.5)
   프롬프트: "이 작업들 분석 + 어떤 viz_kind 가 적절한지 분류 + 데이터 출력"
       ↓
3. LLM 응답 JSON:
   {
     "summary": "한국어 한 줄",
     "viz_kind": "diff | gauge | table | flow | badge | code",
     "viz_data": { ... }
   }
       ↓
4. 브라우저: viz_kind 보고 적절한 렌더러 호출
       ↓
5. 요약 카드 안에 시각 컴포넌트 자동 펼침
```

같은 도구(예: Edit) 라도 작업 내용에 따라 다른 viz_kind:
- "함수 시그니처 변경" → diff
- "테스트 통과 12/15" → gauge
- "마이그레이션 3단계" → flow
- "보안 패치 완료" → badge

---

## 깨서 할 일 (우선순위 순)

### 1. V4 실행해서 결과 보기 (5분)

```bash
cd /Users/daeseonyoo/Documents/GitHub/aicore/viz-agents/v4
./start.sh
```

- 브라우저 자동 열림 (V4 뱃지 확인)
- Claude Code 세션 시작 → 실제 작업 시켜봄
- 요약 카드에 viz_kind에 따라 다른 시각 뜨는지 확인

### 2. 로드맵 검토 (15분)

`viz-roadmap.md` 한 페이지 읽기. V5~V20 그림 잡기.

### 3. V5+ 우선순위 결정

본인 비전 6영역 (코드/시스템/제품/아키텍처/비즈니스/애니메이션) 중
**어디부터 V5+ 실제 빌드** 할지 결정.

추천 순서 (본인 비전 기준):
- **V10 (애니메이션)** ← 본인 처음 비전 단어 "애니메이션처럼" 직격
- **V9 (비즈니스 KPI)** ← 비-엔지니어 가치 큼
- **V6 (시스템 토폴로지)** ← 시각 임팩트 큼

---

## 시간 정직 보고

- 17개 spec 작성: 약 30분
- V4 빌드: 약 30분
- **총 ~1시간** (사전 예측 5-7시간보다 훨씬 빨랐음)

---

## 비용 정직 보고

- 자는 동안 추가 비용: **$0** (코드 작성에 LLM 호출 X — 본인 Claude Code 호출만)
- V4 실행 시 비용:
  - Stop 이벤트마다 LLM 호출 (Claude Haiku 4.5)
  - 1건당 약 $0.0005 (V2의 약 1.5배 — viz_data 추가 출력 토큰)
  - 하루 100건 사용 ≈ 5센트

---

## V4 한계 (정직)

1. **V4d (LLM 자유 HTML/SVG) 미구현** — 보안 sanitize 작업 필요. 별도 빌드.
2. **viz_kind 7개에 제한** — 새 시각 종류 추가하려면 코드 수정 필요.
3. **viz_kind 분류 정확도가 LLM 의존** — 가끔 부적절한 분류 가능.
4. **본인 비전 6영역 중 V4가 닿은 건** — 코드 표면 + 시스템 일부. 제품/아키텍처/비즈니스/애니메이션 거의 미달.

---

## 다음 결정 (본인이 깨서)

```
선택지 A: V4 만 평가, V5 신중하게 한 단계씩
  → 위험 최소, 진척 느림

선택지 B: V10 (애니메이션) 직행
  → 본인 비전 가장 직격, 위험 큼

선택지 C: V5 → V6 → V7 → ... 순차
  → 본인 비전 6영역 차근차근
```

---

## 메모리 업데이트 사항

자는 동안 사용자 비전 명시 더 강해짐:
- "시각화를 하나만 하는 게 아니고 작업 디스크립션에 따라 동적으로"
- "V20까지 한번 짜볼 수 있나"

이 두 가지가 V4 방향 + 로드맵 작성 동기.

→ `~/.claude/projects/.../memory/viz_product_vision.md` 업데이트 권장 (다음 세션 위해).

---

## 정리

- ✅ 17개 spec 문서 = 본인 깨서 검토 후 다음 방향 결정
- ✅ V4 실제 코드 = 본인 깨서 실행 + 평가
- ✅ V5~V20 코드 = NOT NOW. 본인 평가 후 결정.
- ✅ 위험 최소: 평가 없이 빌드한 게 V4 한 개뿐
- ✅ 학습 자료: 17개 spec이 자기설명 컨텐츠 역할

**잘 자요. 깨면 v4/ 실행하고 spec 들 검토하세요.**
