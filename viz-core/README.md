# 🎯 viz-core

> **AI 답변을 텍스트로 못 읽는 사람이 만든 — 본인 학습 자산 시각화 저장소.**

`AI 출력 → viz-core → 사용자의 0.5초 글랜스`
`나의 학습 → library → 다시 떠올릴 때 즉시`

자세한 정의는 [../CORE.md](../CORE.md) 참고.

---

## Why I made this

- 나는 **비-엔지니어. 영어 약함. 텍스트 wall 못 읽음. 집중력 짧음.**
- AI 가 "캐싱 쓰자" "Index 만들자" 추천할 때, 매번 검색 → 시간 낭비.
- AI 출력을 그림으로 한 눈에 보고 싶다 — 옆 탭에서 0.5초에.
- 나 같은 사람 한 명만 있으면 가치 있다는 가정으로 시작.

## How I use it daily

```
1. Claude Code / ChatGPT 에 일 시킴 (코딩 / 분석)
2. AI 답변에 ```viz-spec JSON 자동 박힘 (가이드 박아둠)
3. 옆 탭 viz-core 가 자동 시각화 → 텍스트 안 읽어도 됨
4. 새 개념/시스템 만나면 library/ 에 등록 (영구 자산)
5. 다음에 같은 거 만나면 0.5초에 떠올림
```

## 차별점

| | 흔한 도구 | viz-core |
|---|---|---|
| Chart.js / D3 | 그래픽 엔진 | **빌리는 입장** (vocab 표준화) |
| Mermaid | 도식 라이브러리 | **빌리는 입장** |
| Notion / Obsidian | 텍스트 중심 노트 | **시각 우선** |
| BI 도구 (Tableau...) | 사람이 만든 데이터 | **AI 출력 전용** |
| **viz-core** | — | **AI 출력 → 24종 표준 vocab → 즉시 시각** |

**핵심 발명:** "AI 출력 전용 시각화 vocabulary" — 24종 viz_kind 표준 정의 + LLM 라우팅 + 통합 자산 라이브러리.

## 24종 viz_kind (Phase 1~5)

| Phase | 종류 | 예시 |
|---|---|---|
| 기본 11 | diff/gauge/table/flow/badge/code/animation/kpi/journey/arch/whatif | AI 작업 / 결과 표시 |
| 확장 2 | mermaid / callgraph | 무한 도식 + 코드 |
| Phase 1 (차트) | timeseries / bar / funnel | 비즈 / 마케팅 데이터 |
| Phase 2 (운영) | heatmap / kanban | 운영 / 프로젝트 |
| Phase 3 (분석) | waterfall / cohort | 분산 추적 / retention |
| Phase 4 (PM/UX) | crud / userflow / screenmap / depgraph | 설계 단계 |
| Phase 5 (학습) | **concept** ★ | 기술 개념을 비유 + 시각 + 장단으로 |

## 핵심 페이지

| 경로 | 무엇 | 비고 |
|---|---|---|
| `/` | AI 출력 실시간 시각화 + 메인 작업 | WebSocket |
| `/library.html` | 📚 **내 저장소** — 모든 viz_kind 통합 | 자산 등록/검색/백업 |
| `/concepts.html` | 💡 병신교육소 — 개념 학습 | concept 전용 친절한 폼 |
| `/showcase` | 24종 샘플 갤러리 | 평가용 |
| `/spec` | AI 가이드 + 복붙 프롬프트 | 다른 AI 와 페어링 |
| `/stats` | 📊 사용 통계 — Dogfood 증명 | 캘린더 heatmap + top 자산 |

## 영구 저장 구조

```
library/{viz_kind}/{slug}.json
├── concept/        ← 기술 개념 (캐싱 / Index / JWT / CDN...)
├── depgraph/       ← 본인 시스템 의존도
│   └── viz-core-self.json  ★ 이 도구로 이 도구 시각화 (meta)
├── arch/           ← 본인 아키텍처
├── crud/           ← 본인 권한 매트릭스
└── ... (24종 가능)
```

- 추가: 폼 또는 JSON 직접 편집 (`/library.html`)
- 백업: `/library/export` (zip 다운로드)
- 복원: `/library/import` (zip 또는 JSON 업로드)
- 사용 로그: `usage_log.jsonl` (영구 — Dogfood 증명용)

## 독립 동작

| 외부 의존 | 필요? |
|---|---|
| Anthropic LLM | 자산 등록/조회 시 ❌ — `/viz/request` 자연어 라우팅 시만 ✓ |
| 인터넷 | ❌ (Chart.js/Mermaid CDN 만, 캐시되면 OFF 가능) |
| DB | ❌ 파일 시스템 |
| 다른 AI 도구 | ❌ — 혼자 써도 가치 |

## AI 페어링 (다른 AI 와 자동 시각화)

`/spec` 에서 복붙 프롬프트 받아서 본인 ChatGPT / Claude / Cursor 의 system prompt 에 박기.

이후:
- AI 답변에 ```viz-spec JSON 자동 박힘 (사용자에겐 안 보이게)
- `POST /viz/spec` 으로 답변 텍스트 보내면 → 마커 자동 추출 → 옆 탭 시각화
- **LLM 호출 0** — 빠름 / 무료 / 정확

자세한 가이드: [`AI_GUIDE.md`](./AI_GUIDE.md) 또는 `/spec` 페이지.

## 기술 스택

- **백엔드:** Python 3.11+ / FastAPI / WebSocket / httpx
- **프론트:** Vanilla HTML + JS (프레임워크 X) / Chart.js / Mermaid
- **저장:** 디스크 (JSON 파일) — DB 없음
- **LLM:** Anthropic Claude (옵션 — 자연어 라우팅용만)
- **코드 양:** ~5000 lines (1인 빌드)

## 실행

```bash
cd viz-core
./start.sh
# → http://127.0.0.1:8765
```

API 키 (옵션 — LLM 라우팅 쓸 때):
```bash
echo "sk-ant-..." > .local_key.txt  # gitignore 됨
```

## Dogfood — 진짜 매일 쓰는 증거

`/stats` 에서 확인:
- 캘린더 heatmap (90일)
- 가장 자주 본 자산 top 10
- viz_kind 별 사용 분포
- 사용 시작일 / 마지막 사용

**이게 PMF 시그널 — 본인이 매일 쓰는 도구는 다른 누군가에게도 가치 있을 가능성 ↑.**

## 로드맵 (지금 → 다음)

- [x] 24종 viz_kind vocab 표준
- [x] 통합 라이브러리 시스템 (`library/{kind}/{slug}.json`)
- [x] viz-spec 마커 파서 (LLM 호출 0)
- [x] 백업/복원 (zip)
- [x] 사용 통계 (Dogfood 증명)
- [x] 본인 시스템을 본인 도구로 시각화 (meta)
- [ ] 자동 실행 (`launchd` plist)
- [ ] 친절한 폼 확장 (depgraph/arch/kpi 등)
- [ ] AI 페어 자동 hook 인스톨러
- [ ] (나중) 클라우드 배포 (모바일 접속 필요해질 때)

---

> **만든 사람:** Json_Daeseon_Yoo — 비-엔지니어. 본인을 위해 본인 같은 사람을 위한 도구.
