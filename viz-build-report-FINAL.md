# 🚀 VIZ App — 통합 제품 완성

**작업**: 2026-05-24 새벽 — 사용자 "31개 통합으로 제품처럼 제대로, MD 다 시각화, 애니메이션, 끝까지" 요청 응답

---

## 한 줄

`viz-agents/viz-app/` 폴더 = **v0~v30 모든 기능 통합 + MD 파일 시각화 + 진짜 애니메이션**.
이 폴더 하나만 실행하면 31개 버전 다 쓰는 것과 같음.

---

## 실행 (한 줄)

```bash
cd /Users/daeseonyoo/Documents/GitHub/aicore/viz-agents/viz-app && ./start.sh
```

자동:
- 이전 v* 폴더의 키 자동 복사
- 브라우저 자동 열림
- 모든 hooks 설치 (이미 있으면 스킵)

---

## 한 화면에 보이는 모든 것

```
좌측 (메인):                          우측 (사이드바, 350px 고정):
├─ 헤더                                ├─ 📄 Docs 탭
│  ● 상태  events  LLM  👥  $비용     │   - viz-roadmap.md
│  [⚙️키] [📷] [🎬] [⊕PR] [🌗]        │   - viz-v4.md
├─ 지금: ⚡ pytest 실행 중             │   - viz-v5.md
├─ 💬 자연어 시각 요청 [생성]          │   ... (전체 viz-*.md)
├─ ⏱ Time Travel: [─────●──] 현재      │   (클릭하면 내용 표시)
├─ 세션 박스 (에이전트별 색)            │
│  ▼                                   ├─ 📊 토폴로지 탭
│  💬 사용자                            │   - 만진 .py 파일 그래프
│  ▼                                   │   - SVG force graph
│  📖 Read                              │
│  ▼                                   ├─ ⭐ 즐겨찾기 탭
│  🎯 코드 품질 7/10                    │   - 별표 클릭한 시각들
│  ▼                                   │
│  🔒 보안 medium 경고                  │
│  ▼                                   │
│  📝 활동 요약 + viz_kind 자동 시각    │
│   - 👍 👎 ⭐ 버튼                     │
│  ▼                                   │
│  📊 일일 회고 (12h)                   │
│                                      │
└─ 배경에 작은 입자들이 천천히 떠오름 (애니메이션) ─┘
```

---

## 통합된 기능 (전수)

### v0-v4: 기본 HUD
- Hook 이벤트 실시간 수신 (WebSocket)
- 카드 timeline + 세션 박스 그래프
- NOW 큰 박스 (지금 뭐 하나)
- LLM 활동 요약 + viz_kind 자동 선택
- 키 모달 (디스크 저장)

### v5-v11: viz_kind 컴포넌트 (LLM이 선택, 진짜 시각)
- `diff` 빨강/초록 패치
- `gauge` 큰 숫자 + 진행 바
- `table` 데이터 표
- `flow` 단계 + 화살표
- `badge` 색 알약 (성공/실패)
- `code` 코드 스니펫
- **`animation` SVG path + 점이 흐름** ★
- `kpi` 비즈니스 메트릭 그리드
- `journey` 사용자 여정 + 이탈%
- `arch` 아키텍처 레이어
- `whatif` 현재 vs 변경 후

### v12-v20: UX 기능
- 더블클릭 → drill-down 모달
- agent_id 컬러 (SI/QA/OPS/ADR/DOC/AUTO/Claude)
- 자연어 시각 요청 입력 박스
- 👥 시청자 카운트
- 모바일 반응형
- 📷 PNG 캡처 (html2canvas)
- ⏱ 시간 슬라이더 (과거 시점 표시)
- 👍 👎 피드백 (.feedback.jsonl)

### v21-v30: 도구/통합
- 우클릭 → 클립보드 (Claude에 컨텍스트 전달)
- Webhook 알림 (`WEBHOOK_URL` 환경변수)
- 🎬 30초 화면 녹화 (MediaRecorder)
- ⊕ GitHub PR 자동 시각화
- 🎯 자동 코드 품질 LLM 점수
- 🔒 자동 보안 LLM 체크
- $비용 트래커 (실시간 누적)
- 📊 12h 자동 회고
- ⭐ 즐겨찾기 (.favorites.jsonl)
- 🌗 다크/라이트 테마 토글

### ★ viz-app 신규 (통합에서만)
- **MD 파일 watcher** — viz-*.md 파일 변경 감지 → 카드로 broadcast
- **MD 사이드바** — 모든 viz-*.md 목록 + 클릭하면 내용 표시
- **3-탭 사이드바** — Docs / Topology / Favorites
- **배경 파티클 애니메이션** — 작은 점들이 천천히 떠오름
- **NOW 박스 scan 라인** — 가로 빛이 지나가는 효과
- **세션 dot glow** — 펄스 효과
- **카드 hover** — 살짝 우측으로 슬라이드

---

## 폴더 구조

```
viz-agents/
├── 🚀 viz-app/                ← 이걸 실행 (통합 제품)
│   ├── server.py              36 KB — 모든 endpoint
│   ├── index.html             68 KB — 모든 시각 + 애니메이션
│   ├── install_hooks.py
│   ├── uninstall_hooks.py
│   ├── start.sh
│   └── README.md
├── v0~v30/                    31개 학습용 폴더 (개별 단계)
├── viz-roadmap.md             V4~V20 전체 그림
├── viz-v4.md ~ viz-v20.md     17개 spec
├── viz-build-report.md        V4 까지
├── viz-build-report-2.md      V5-V20 표면
├── viz-build-report-3.md      V5-V20 진짜 빌드
├── viz-build-report-4.md      V21-V30 추가
└── viz-build-report-FINAL.md  ← 지금 이 파일 (통합)
```

---

## 엔드포인트 전수

| Method | Path | 역할 |
|---|---|---|
| GET | / | index.html |
| GET | /healthz | 상태 (clients/events/LLM/cost/key_source/webhook) |
| GET | /ws | WebSocket (이벤트 실시간 push) |
| POST | /event | Hook 이벤트 수신 |
| GET | /key/status | 키 상태 |
| POST | /key | 키 저장/삭제 |
| POST | /key/test | 키 작동 테스트 |
| GET | /history | 시간축 이벤트 (V19) |
| GET | /topology | .py import 그래프 (V6) |
| GET | /docs | viz-*.md 목록 (★ NEW) |
| GET | /docs/{name} | MD 내용 (★ NEW) |
| POST | /feedback | 👍👎 (V20) |
| POST | /favorite | ⭐ 즐겨찾기 (V29) |
| GET | /favorites | 즐겨찾기 목록 |
| GET | /cost | 비용 (V27) |
| POST | /viz/request | 자연어 시각 요청 (V15) |
| POST | /github/pr | GitHub PR 시각화 (V24) |

---

## 시간 / 비용

- 통합 빌드: 약 1시간
- 추가 LLM 비용: $0
- 사용자가 실행하면 LLM 비용 발생 (Haiku 4.5):
  - 일반 활동 요약: $0.0005/건
  - 코드 품질 자동: $0.0003/건
  - 보안 자동: $0.0004/건
  - 자연어 요청: $0.001/건
  - 회고 (12h): $0.002/건
  - **하루 사용 추정: $0.10 ~ $1.00 (작업량에 따라)**

---

## 깨서 첫 명령

```bash
cd /Users/daeseonyoo/Documents/GitHub/aicore/viz-agents/viz-app && ./start.sh
```

브라우저 자동 열림. 진짜 통합 제품 보임.

본인이 처음 말한 비전:
> "코드, 시스템, 제품, 아키텍처, 비즈니스를 전부 시각화해서 애니메이션처럼 보여주고, 사용자가 텍스트 wall을 읽지 않고 바로 이해하게 한다."

**viz-app 이 그 비전의 첫 통합 구현.** 완벽하진 않지만 31개 흩어진 기능을 한 화면에 모음 + MD까지 시각화 + 진짜 애니메이션.

---

## 알려진 한계 (정직)

1. 토폴로지는 단순 원형 (D3 force-graph 아님)
2. 회고는 12시간 idle 후 자동 (즉시 X)
3. MD watcher 는 3초 폴링 (inotify 아님)
4. 다중 사용자 collab은 같은 WebSocket 다중 접속만
5. 모바일에서는 사이드바 위로 이동 (좁아짐)
6. CDN(html2canvas) 의존 — 오프라인 X

---

**잘 자요. 깨면 `viz-app/start.sh` 한 번만 돌리고 옆 창 봐주세요.**
