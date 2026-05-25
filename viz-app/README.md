# 🚀 VIZ App — Integrated Live HUD

**v0~v30의 모든 기능을 하나의 통합 제품으로.**
Claude Code 작업 + MD 파일 + 시스템 토폴로지 + 모든 시각화 + 진짜 애니메이션.

## 실행

```bash
cd /Users/daeseonyoo/Documents/GitHub/aicore/viz-agents/viz-app
./start.sh
```

브라우저 자동으로 `http://localhost:8765` 열림.
v20 등 다른 폴더에서 키 설정한 적 있으면 자동 복사.

## 한 화면에 다 보이는 것

```
┌─ 헤더 ───────────────────────────────────────────────┬─ MD 사이드바 ─┐
│ ● 상태  events │ LLM │ 👥 시청자 │ $비용 │ 버튼들 │ APP  │ 📄 Docs       │
├──────────────────────────────────────────────────────│ [MD/토폴/즐겨] │
│ 지금: ⚡ 명령 실행 중                                  │                │
│ pytest tests/ -v                                     │ viz-roadmap.md │
├──────────────────────────────────────────────────────│ viz-v4.md      │
│ 💬 [자연어 시각 요청 입력]                  [생성]    │ ...            │
├──────────────────────────────────────────────────────│ viz-v20.md     │
│ ⏱ Time: [─────●──] 현재                              │                │
├──────────────────────────────────────────────────────│ [선택한 내용]  │
│ ┌─ 세션 Claude (파랑) ──── 12개 ────────────────────┐│                │
│ │ 💬 사용자 메시지                                   ││                │
│ │ ▼                                                  ││                │
│ │ 📖 Read api.py                                     ││                │
│ │ ▼                                                  ││                │
│ │ 🎯 코드 품질 7/10 — 적절히 모듈화                  ││                │
│ │ ▼                                                  ││                │
│ │ 🔒 보안 medium — SQL injection 가능성 있음         ││                │
│ │ ▼                                                  ││                │
│ │ 📝 활동 요약 [LLM] 5events viz: animation          ││                │
│ │   "verify_password 함수 보안 강화"                 ││                │
│ │   [SVG 애니메이션: 점이 노드 사이 흐름]            ││                │
│ │   👍 👎 ⭐                                          ││                │
│ │ ▼                                                  ││                │
│ │ 📊 일일 회고 (12시간) — 3건 처리, ...               ││                │
│ └────────────────────────────────────────────────────┘│                │
│ ┌─ 세션 SI (초록) ─── 다른 에이전트도 같이 ──────────┐│                │
└──────────────────────────────────────────────────────┴────────────────┘
        + 배경 파티클이 천천히 위로 흐름 (애니메이션)
```

## 통합된 기능 (v0~v30)

| 기능 | 원래 버전 |
|---|---|
| 카드 timeline + 세션 박스 + ▼ 연결선 | v0~v3 |
| LLM 활동 요약 + viz_kind | v4 |
| Python symbol diff (regex) | v5 |
| /topology endpoint + 사이드 SVG 그래프 | v6 |
| viz_kind: journey/arch/kpi | v7-v9 |
| viz_kind: animation (★ SVG path) | v10 |
| viz_kind: whatif | v11 |
| 더블클릭 → drill-down 모달 | v12 |
| agent_id 컬러 매핑 (SI/QA/OPS/...) | v13 |
| Multi-pane (MD 사이드바로 통합) | v14 |
| 자연어 시각 요청 (/viz/request) | v15 |
| 👥 시청자 카운트 | v16 |
| 모바일 적응 CSS | v17 |
| 📷 PNG 캡처 | v18 |
| ⏱ 시간 슬라이더 (/history) | v19 |
| 👍👎 피드백 (/feedback) | v20 |
| 우클릭 → 클립보드 | v21 |
| Webhook 알림 (WEBHOOK_URL env) | v22 |
| 🎬 30초 화면 녹화 | v23 |
| ⊕ PR — GitHub 시각화 (/github/pr) | v24 |
| 🎯 자동 코드 품질 LLM 점수 | v25 |
| 🔒 자동 보안 LLM 체크 | v26 |
| $비용 트래커 (/cost) | v27 |
| 📊 12h 자동 회고 | v28 |
| ⭐ 즐겨찾기 (/favorite) | v29 |
| 🌗 다크/라이트 테마 | v30 |
| **★ NEW** MD 파일 실시간 watcher + 사이드바 | viz-app |
| **★ NEW** 배경 파티클 애니메이션 | viz-app |
| **★ NEW** 우측 사이드바 3-탭 (MD/토폴/즐겨찾기) | viz-app |

## 환경 변수 (선택)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # 또는 UI에서 ⚙️ 키
export WEBHOOK_URL="https://hooks.slack.com/..."   # Stop 시 알림
```

## 핵심 단축키
- `Cmd+Shift+R` 강력 새로고침
- 노드 **우클릭** → 클립보드 복사
- 노드 **더블클릭** → drill-down 모달
- 시간 슬라이더 이동 → 과거 시점 카드만 표시
- ⌨ Enter (자연어 입력) → 즉시 시각 생성

## 한계
- v6 토폴로지는 단순 원형 (D3 force-directed 아님)
- 비용은 Haiku 4.5 가격 가정
- MD watcher는 3초 폴링 (inotify 아님)
- 회고는 12시간 idle 후 자동 (즉시 X)
- 다중 사용자 collab은 같은 WebSocket 다중 접속만 (사용자별 권한 X)
