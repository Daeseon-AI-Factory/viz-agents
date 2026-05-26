# 09. iframe + 외부 플랫폼 연동

> **viz-core 를 ddalkkak 같은 외부 페이지에 끼워 넣는 원리.**

---

## 한 줄

> iframe = HTML 안 작은 액자. 그 안에 다른 사이트 통째 들어감.

---

## 가장 단순 — HTML 한 줄

```html
<iframe src="http://localhost:8765" 
        width="100%" 
        height="800px"
        style="border:none;">
</iframe>
```

이게 끝. ddalkkak 어디든 이 한 줄 박으면 viz-core 가 그 자리에 보임.

---

## 작동 원리

```
[사용자 브라우저]
     │
     │ 1. ddalkkak 요청
     ▼
[ddalkkak 서버]
     │
     │ 응답: HTML (안에 <iframe src="viz-core"/>)
     ▼
[브라우저]
     │
     │ 2. iframe 발견 → viz-core 도 요청
     ▼
[viz-core 서버]
     │
     │ 응답: viz-core HTML
     ▼
[브라우저]
     │ 3. 두 페이지 동시 렌더
     │
     ▼
   한 화면에 두 사이트 보임
```

---

## 데이터 통신 3가지

### 1. URL 파라미터 (가장 단순)

ddalkkak 측:
```html
<iframe src="http://viz-core:8765?workspace_id=abc&user=daeseon"/>
```

viz-core 측 (JS):
```js
const params = new URLSearchParams(location.search);
const workspaceId = params.get("workspace_id");  // "abc"
```

### 2. postMessage (양방향, 강력)

ddalkkak 측 (부모):
```js
const iframe = document.querySelector("iframe");
iframe.contentWindow.postMessage({
  type: "viz_request",
  payload: { /* 데이터 */ }
}, "*");
```

viz-core 측 (자식, iframe 안):
```js
window.addEventListener("message", (e) => {
  if (e.data?.type === "viz_request") {
    console.log("ddalkkak이 보낸 데이터:", e.data.payload);
  }
});
```

### 3. REST API (가장 풍부)

ddalkkak 백엔드 → viz-core 백엔드 직접 호출 (iframe 통신 X):
```python
# ddalkkak 안에서
import httpx
async with httpx.AsyncClient() as client:
    await client.post(
        "http://viz-core:8765/event",
        json={"hook_event_name": "...", ...}
    )
```

viz-core 는 받아서 자동 시각 → WebSocket 으로 모든 브라우저 broadcast.

---

## 어떻게 골라?

| 시나리오 | 추천 |
|---|---|
| 단순 — 사용자가 viz-core 화면을 ddalkkak 안에서 보고 싶음 | **iframe + URL 파라미터** |
| ddalkkak이 viz-core 에 데이터 보냄 | postMessage 또는 REST |
| ddalkkak 백엔드가 자동으로 시각 트리거 | **REST POST /event** |
| 풀 통합 (사용자 인증 공유 등) | iframe + postMessage + REST 다 |

---

## ★ 실제 ddalkkak 통합 시나리오

### 시나리오 A: 본인 페이지에 viz 사이드바
```
[ddalkkak 메인]                     [iframe — viz-core]
워크스페이스 선택                     ●●● 작업 중
새 작업 생성                          🔄 변경 감지...
파일 편집                            📝 활동 요약
   ↓ 작업 발생                       📦 callgraph 시각
   ↓ POST /event 자동                
```

### 시나리오 B: 토글 버튼
```
ddalkkak 화면에 "📊 시각화 보기" 버튼
   클릭 → 화면 우측에 iframe 슬라이드
   다시 클릭 → 숨김
```

---

## 보안 주의

### X-Frame-Options
- 서버가 iframe 안에서 보이는 거 허용/거부
- FastAPI 기본 = 허용 (viz-core OK)
- 어떤 사이트 (`<meta http-equiv="X-Frame-Options" content="DENY">`) 는 iframe 못 끼움

### CORS (Cross-Origin Resource Sharing)
- 다른 도메인 API 호출 허용 여부
- ddalkkak (a.com) 에서 viz-core (b.com) POST 부르려면:
  - viz-core 가 `Access-Control-Allow-Origin: a.com` 헤더 보내야
- 같은 도메인 (localhost) 이면 신경 X

### iframe sandbox
- `<iframe sandbox="allow-scripts allow-same-origin"/>` 처럼
- 권한 제한 가능

---

## 통합 단계 (지금 → 미래)

### 1단계: 같은 머신 (개발)
```html
<!-- ddalkkak/frontend/.../page.tsx -->
<iframe src="http://localhost:8765" width="100%" height="800px"/>
```
→ 본인 머신에서 둘 다 돌면 작동.

### 2단계: docker-compose (배포)
```yaml
# ddalkkak/docker-compose.yml
services:
  ddalkkak:
    ...
  viz-core:
    build: ../viz-agents/viz-core
    ports:
      - "8765:8765"
```
→ docker-compose up 한 번에 둘 다.

### 3단계: 서브도메인 (운영)
```
ddalkkak: https://ddalkkak.daeseon.ai
viz-core: https://viz.ddalkkak.daeseon.ai (서브도메인)

iframe src = "https://viz.ddalkkak.daeseon.ai"
+ 같은 부모 도메인 → CORS / iframe 정책 자유
```

### 4단계: 인증 통합
- ddalkkak 의 JWT/쿠키를 viz-core 도 인식
- 또는 ddalkkak 이 viz-core 에 토큰 발급 후 iframe URL 에 박음

---

## 핵심 이해 체크

- [ ] iframe = 한 페이지 안 작은 액자
- [ ] HTML 한 줄로 끝
- [ ] 데이터 통신 = URL param / postMessage / REST 3가지
- [ ] 같은 도메인 = 자유 / 다른 도메인 = CORS 신경
- [ ] 분리 유지 + iframe = 가장 깔끔한 통합
