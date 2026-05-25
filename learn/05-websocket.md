# 05. WebSocket 실시간 push (어떻게 즉시 보이나)

> **이걸 모르면 "왜 새로고침 안 해도 카드가 떠?" 모름.**

---

## 한 줄

> 브라우저가 서버와 **상시 연결** 유지. 서버에서 이벤트 발생 → 브라우저로 즉시 전송.

---

## HTTP vs WebSocket 차이

```
일반 HTTP:                     WebSocket:
  요청 → 응답 → 끊김             요청 → 연결 유지 (계속 켜져있음)
  
  사용자가 새로고침해야           서버가 보내면 즉시 도착
  새 데이터 봄                  사용자는 가만히 있어도 됨
```

---

## viz-core 의 WebSocket 흐름

```
1. 사용자 브라우저 열음
        ↓
2. JavaScript: new WebSocket("ws://localhost:8765/ws")
        ↓
3. 서버: accept → 연결 유지
        ↓
4. 서버가 client 리스트에 추가
   _clients.add(this_socket)
        ↓
5. ━━━ 이제 항상 켜진 상태 ━━━
        
   서버 어디서든 _broadcast(record) 호출하면:
        ↓
   for client in _clients:
       client.send_json(record)
        ↓
   ★ 모든 연결된 브라우저에 즉시 도착
        ↓
   JavaScript ws.onmessage(event):
       add(event.data)  ← 화면에 카드 추가
```

---

## 실제 코드 (단순화)

### 서버
```python
@app.websocket("/ws")
async def ws(socket: WebSocket):
    await socket.accept()
    _clients.add(socket)  # 클라이언트 등록
    try:
        # 최근 150개 이벤트 먼저 보내기 (페이지 새로 연 사람)
        for ev in _history[-150:]:
            await socket.send_json(ev)
        # 연결 유지
        while True:
            await socket.receive_text()  # ping 대기
    finally:
        _clients.discard(socket)

async def _broadcast(record):
    for c in list(_clients):
        try:
            await c.send_json(record)
        except:
            pass  # 끊긴 client 무시
```

### 브라우저
```javascript
let ws = new WebSocket(`ws://${location.host}/ws`);

ws.onopen = () => { /* 연결됨 */ };

ws.onmessage = (e) => {
  const event = JSON.parse(e.data);
  add(event);  // 카드 화면에 추가
};

ws.onclose = () => {
  setTimeout(connect, 1500);  // 끊기면 1.5초 후 재연결
};
```

---

## 왜 WebSocket?

| 방식 | 장단점 |
|---|---|
| 폴링 (1초마다 GET) | 단순. 1초 지연. 트래픽 많음. |
| Long polling | 중간. 연결 다시 맺음. |
| **WebSocket (지금)** | **실시간. 효율적. 양방향.** |
| Server-Sent Events | 단방향만. 비슷한 성능. |

viz-core 는 실시간 글랜스가 핵심 가치 → WebSocket 적합.

---

## 여러 브라우저 동시 연결

```
브라우저 1 (Mac Safari)     ─┐
브라우저 2 (Mac Chrome)     ─┤  → 같은 WebSocket /ws
브라우저 3 (휴대폰)         ─┘     모두 _clients 안에

서버가 broadcast 하면:
  모든 브라우저 동시에 같은 카드 봄
```

→ 본인이 브라우저 탭 여러 개 열면 모두 sync.
→ 휴대폰에서 같은 LAN 으로 접속해도 sync.

---

## 끊기면?

```
ws.onclose 이벤트 발생
   ↓
1.5초 후 자동 재연결 시도
   ↓
연결되면 서버가 최근 150개 이벤트 다시 보냄
   ↓
끊긴 동안 놓친 카드 다시 채워짐
```

→ 네트워크 잠깐 끊겨도 자동 복구.

---

## 비용

WebSocket 자체 비용 $0. 본인 머신 안에서만 도는 거.

대역폭도 적음 — JSON 메시지 1개 = 1-5KB.

---

## 한계

- 단일 머신 (localhost) — 외부 사용자 X (의도적)
- 인증 X — localhost니까 안전 (외부 노출하면 위험)
- 메모리 history 500개 (디스크 영속 X)

---

## 핵심 이해 체크

- [ ] WebSocket = 상시 연결 (vs HTTP = 요청/응답 끝)
- [ ] 서버 broadcast → 모든 브라우저 즉시
- [ ] 끊기면 자동 재연결 + history 복구
- [ ] localhost 만 → 외부 X
- [ ] 비용 0

다음: [06-data-flow.md](./06-data-flow.md)
