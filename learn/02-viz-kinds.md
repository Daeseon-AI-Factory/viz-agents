# 02. 11종 viz_kind (시각 vocabulary)

> **이게 viz-core의 핵심 단어장. 11개만 알면 모든 시각 이해.**

---

## 왜 11종인가

사용자가 진짜 봐야 할 시각의 종류는 무한 X. 11가지로 99% 커버 가능.
새 종류 필요하면 추가하되, **무작정 늘리지 않음**.

---

## 11종 vocabulary

### 1. `diff` — 코드 변경
```
[빨강 BEFORE]    [초록 AFTER]
- return None    + return result
```
**언제**: Edit/Write 발생 시. 함수 시그니처 변경, 보안 패치 등.
**데이터**: `{ file, before, after, lang }`

---

### 2. `gauge` — 단일 수치
```
테스트 통과율
  12 / 15 통과
  [████████░░] 80%
```
**언제**: 테스트 결과, 점수, 진행률, 응답시간 등.
**데이터**: `{ label, value, max, unit }`

---

### 3. `table` — 여러 항목
```
| 함수 | 줄  | 인자 |
| api  | 12  | x    |
| db   | 45  | conn |
```
**언제**: 검색 결과, 파일 목록, 데이터 비교.
**데이터**: `{ headers, rows }`

---

### 4. `flow` — 순서 단계
```
[빌드] → [테스트] → [배포] → [모니터링]
  ✓        ✓        ▶        ○
 done     done     now      todo
```
**언제**: 배포, 마이그레이션, 워크플로우.
**데이터**: `{ steps: [{name, status}] }`

---

### 5. `badge` — 단일 상태
```
[ ✓ 통과 ]   [ ⚠️ 경고 ]   [ ❌ 실패 ]
```
**언제**: 성공/실패, 활성/비활성 같은 한 마디.
**데이터**: `{ label, tone }`

---

### 6. `code` — 코드 스니펫
```python
def verify_password(p, h):
    return secrets.compare_digest(p, h)
```
**언제**: 짧은 코드 강조.
**데이터**: `{ lang, code }`

---

### 7. `animation` — 흐름 애니메이션 ★ (본인 비전 핵심)
```
[API] ──●──→ [Service] ──●──→ [DB]
       (점이 노드 사이 흐름, SVG animateMotion)
```
**언제**: 데이터 흐름, 서비스 호출 순서.
**데이터**: `{ nodes: [{id, label}], flow: [id...], duration_ms }`

---

### 8. `kpi` — 비즈니스 메트릭
```
┌─ MRR ─┐ ┌─ 사용자 ─┐ ┌─ 전환 ─┐
│ $52K  │ │ 1,240    │ │ 3.2%   │
│ ▲ 2%  │ │ ▼ 0.8%   │ │ ━      │
└───────┘ └──────────┘ └────────┘
```
**언제**: 비즈니스 지표 여러 개 한 번에.
**데이터**: `{ kpis: [{label, value, trend, delta}] }`

---

### 9. `journey` — 사용자 여정
```
👤 → [가입] → [결제] → [사용] → [재구독]
              ↓ 12% 이탈
```
**언제**: 사용자 행동 단계.
**데이터**: `{ persona, stages: [{name, icon, drop}] }`

---

### 10. `arch` — 아키텍처 레이어
```
▓ Frontend Layer
  [Next.js] [CDN]
       ▼
▓ API Layer ⚡ active
  [FastAPI]
       ▼
▓ Data
  [Postgres] [Redis]
```
**언제**: 시스템 컴포넌트, 인프라 구조.
**데이터**: `{ layers: [{name, components}], active_layer }`

---

### 11. `whatif` — 변경 영향 예측
```
현재            변경 후
─────           ─────
응답: 320ms    응답: 380ms (⚠️)
실패: 2.3%     실패: 0.8% (✓)

💡 추천: 적용 + DB 풀 늘리기
```
**언제**: "이거 적용하면 어떻게 됨" 시뮬레이션.
**데이터**: `{ title, current, after, recommendation }`

---

### 보조: `callgraph` (코드 분석 추가)
호출 그래프 — 함수들 사이 호출 관계 + 점 흐름 애니.

---

## LLM이 어떻게 선택하나

```
Claude Code 가 작업 시퀀스 끝남 (Stop 이벤트)
   ↓
viz-core 가 그 시퀀스를 LLM에 보냄
   ↓
프롬프트: "이 작업 어떤 viz_kind 가 적합하나? JSON 으로 출력"
   ↓
LLM 응답:
   {
     "summary": "한 줄 요약",
     "viz_kind": "diff" ,  ← 11개 중 선택
     "viz_data": { ... 그 종류 schema 맞춰서 }
   }
   ↓
브라우저: viz_kind 보고 적합 렌더러 호출
```

예시:
- 코드 수정 → LLM 이 "diff" 선택
- 테스트 결과 → "gauge"
- 배포 순서 → "flow"
- 마이크로서비스 호출 → "animation"

---

## 잘못 선택하면?

LLM 이 부적합 viz_kind 선택 → 빈약한 시각. 가능성 항상 있음.
**해결책**:
- 👍 👎 피드백 누적 (V20 기능)
- 더 명확한 시스템 프롬프트
- 본인이 자연어로 직접 요청 (`/viz/request`)

---

## 핵심 이해 체크

- [ ] 11종 vocabulary 각자 언제 쓰는지
- [ ] LLM 이 viz_kind 자동 선택
- [ ] viz_data 는 viz_kind 별 schema 다름
- [ ] 잘못 선택 가능성 있음

다음: [03-llm-call.md](./03-llm-call.md)
