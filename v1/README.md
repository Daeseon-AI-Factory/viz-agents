# VIZ V1 — Claude Code Live HUD (선택지 카드 + 세션 구분)

V0 에서 두 가지 추가:

## V0 → V1 변경점

### 1. AskUserQuestion 시각 카드 렌더링
V0에서는 한 줄 텍스트로만 보여줬던 선택지가, V1에서는 **카드 그리드**로 펼쳐집니다.

```
V0:
  ❓ AskUserQuestion   "자동화 수준을 어디까지?"        [클릭하면 JSON]

V1:
  ❓ AskUserQuestion   자동화 수준을 어디까지?
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ ✨ 풀 자동    │ │ ⚙️ 서버만   │ │ 🛑 수동       │
    │ [추천]        │ │              │ │              │
    │ launchd +    │ │ launchd만    │ │ ./start.sh   │
    │ Chrome 시작   │ │ 본인이 탭 열기│ │ 매번 수동     │
    │ ┌─ preview ─┐│ │ ┌─ preview ─┐│ │ ┌─ preview ─┐│
    │ │ ascii 그림 ││ │ │ ascii 그림 ││ │ │ ascii 그림 ││
    │ └──────────┘│ │ └──────────┘│ │ └──────────┘│
    └──────────────┘ └──────────────┘ └──────────────┘
```

- label, description, preview 모두 시각화
- `(추천)`/`(Recommended)` 자동 감지 → 초록 강조
- multiSelect 표시 (▢ 다중 선택 가능)

### 2. 세션별 색 구분
여러 Claude Code 세션이 동시에 동작해도 색으로 구분:

- 각 카드 좌측에 작은 컬러 dot — `session_id` 해시 → HSL hue
- 헤더에 활성 세션 chips (최근 60초 안에 활동한 세션만)
- 같은 세션은 항상 같은 색

## 동일점 (V0와 같음)
- 같은 포트 `8765`
- 같은 hooks (V0/V1 공용 태그 `VIZ_V0_HUD`)
- 같은 endpoint `POST /event`

→ **V0 hooks 이미 박혀있으면 V1 hook 설치 단계는 자동으로 스킵.**

## 사용법

V0 서버 떠있으면 자동으로 종료시킴 (같은 포트 사용).

```bash
cd viz-agents/v1
./start.sh
```

## V1의 한계 (V2 후보)
- 세션 chips 클릭으로 필터링은 안 됨 (chips만 표시)
- 옵션 카드에서 사용자가 직접 선택할 수는 없음 (Claude Code 본체가 함, VIZ는 표시만)
- 카드 간 연결선 없음 (이 Read → 이 Edit 으로 이어졌다 표시 없음)
- 파일 트리 사이드패널 없음
- 토큰/비용 정보 없음
