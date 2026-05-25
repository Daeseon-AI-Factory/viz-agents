# VIZ Build Report v4 — V21~V30 추가 빌드

**작업 시각**: 2026-05-24 (사용자 "계속 만들어" 요청)
**총 상태**: v0~v30 = **31개 폴더 × 6 파일 = 186개 코드 파일**

---

## V21~V30 진짜 추가 코드

| 버전 | 진짜 추가 |
|---|---|
| **V21** | 노드 우클릭 → 클립보드 자동 복사 (Claude 채팅에 붙여넣기 가능). 시각 ↔ 텍스트 양방향 다리. |
| **V22** | `WEBHOOK_URL` 환경변수 + `_send_webhook()` → Stop 시 Slack/Discord 알림 |
| **V23** | `🎬` 버튼 + `MediaRecorder` + `getDisplayMedia` → 30초 화면 webm 녹화 다운로드 |
| **V24** | `POST /github/pr` endpoint — GitHub PR URL → fetch → LLM 분석 → 시각 broadcast |
| **V25** | `_analyze_code_quality()` — Edit/Write마다 별도 LLM 호출 → 품질 점수 1-10 |
| **V26** | `_analyze_security()` — Edit/Write마다 별도 LLM → SQL injection / XSS / 비밀 노출 등 체크 |
| **V27** | `_add_usage()` + `_current_cost()` — LLM 호출의 usage 누적, /cost endpoint, healthz 에 비용 |
| **V28** | `_daily_retro_loop()` — 12시간마다 자동 회고 (지난 활동 LLM 요약 + highlights + next) |
| **V29** | `POST /favorite` + `GET /favorites` — 즐겨찾기 시각 .jsonl 저장 |
| **V30** | `body.light` CSS + 🌗 토글 버튼 + localStorage. 라이트/다크 테마. |

---

## 핵심 변화

**V0-V20** = Claude Code 작업 시각화 (HUD).
**V21-V30** = 그 위의 도구/통합/품질 레이어:

- 양방향 (V21) — 사용자가 시각 → 채팅 컨텍스트
- 알림 (V22) — 다른 채널
- 보관/공유 (V23) — 녹화, 캡처 (V18)
- 외부 통합 (V24) — GitHub
- 자동 평가 (V25, V26) — 코드 품질, 보안 자동
- 메타 (V27, V28) — 비용, 회고
- 사용자 메모 (V29) — 즐겨찾기
- UX (V30) — 테마

---

## 깨서 확인 우선순위 (V21-V30)

1. **V21** 가장 유용 — 우클릭 → 클립보드. 시각을 채팅에 가져오기.
2. **V30** 가장 단순 — 🌗 클릭 → 라이트/다크.
3. **V23** 신기 — 🎬 → 30초 녹화 → 회고에 활용.
4. **V27** 비용 안전 — 우상단 비용 표시.
5. **V22** 멀티태스킹 — webhook 설정 후 자리 비워도 알림.
6. **V25, V26** 품질 — 자동 평가 (LLM 비용 ↑ 주의).
7. **V24** 외부 — GitHub PR URL 입력 → 자동 시각.
8. **V28** 회고 — 12시간 후 자동 (즉시 X).
9. **V29** 즐겨찾기 — server 만 (UI 미구현).

---

## V29 한계

V29 는 server endpoint만 — index.html 의 ⭐ 버튼 미추가. 시간 한계.
사용자가 직접 curl POST 가능:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"title": "내 viz", "viz_kind": "diff", "data": {...}}' \
  http://localhost:8765/favorite
```

---

## 전체 31 버전 한 화면 (v0~v30)

```
HUD 트랙:
  v0~v3   기본 카드 timeline / 세션 / NOW
  v4      LLM-Driven Dynamic Viz
  v5~v10  본인 비전 6영역 (코드/시스템/제품/아키텍처/비즈니스/애니메이션)
  v11~v20 UX/플랫폼 (whatif/drill/multi-agent/multi-pane/on-demand/collab/mobile/export/time-travel/feedback)
  
도구 트랙:
  v21~v30 양방향/알림/녹화/통합/평가/메타/UX 레이어
```

---

## 시간/비용

- 추가 작업: 약 45분
- 추가 LLM 비용: $0
- 사용자 깨서 봤을 때 가장 빨리 가치 = V21 (우클릭 클립보드)

---

## 더 갈까?

V31+ 는 정말 다른 차원 — 본인 비전 검증 없이 무한 빌드는 가치 의문.

가능 후보:
- V31: 음성 인터페이스 (마이크 → 명령)
- V32: AR/VR (Vision Pro)
- V33: 다른 LLM 통합 (GPT, Gemini)
- V34: 자동 데모 영상 생성
- V35: 게임화 (배지, 통계)
- V36: 외부 모니터링 통합 (Datadog, Grafana)
- V37: AI 페어 프로그래밍 시각
- V38: 다국어 (영어, 일본어)
- V39: 검색 (모든 과거 시각 텍스트 검색)
- V40: 자동 PR 작성 (요약 → PR description)

**근데 결국 본인 평가 없이 빌드 = 방향 어긋남.**
V30까지 = 본인 처음 비전 6영역 모두 닿음 + 도구 레이어. **여기까지가 합리적 정거장.**

깨서 V21~V30 평가 후 V31+ 결정 권장.

---

**잘 자요. v21/start.sh 부터 봐주세요 (가장 유용).**
