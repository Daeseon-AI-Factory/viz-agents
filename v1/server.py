"""VIZ V1 — Claude Code Live HUD server.

V0와 동일한 백엔드. V1의 변화는 전부 index.html(렌더링) 에 있음.
- session_id 별 색 구분
- AskUserQuestion 옵션을 시각 카드로 펼침
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

HERE = Path(__file__).parent
MAX_HISTORY = 500

app = FastAPI(title="VIZ V1 Live HUD")
_clients: set[WebSocket] = set()
_history: list[dict[str, Any]] = []
_lock = asyncio.Lock()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(HERE / "index.html")


@app.get("/healthz")
async def health() -> dict[str, Any]:
    return {"ok": True, "version": "v1", "clients": len(_clients), "events": len(_history)}


@app.websocket("/ws")
async def ws(socket: WebSocket) -> None:
    await socket.accept()
    _clients.add(socket)
    try:
        async with _lock:
            recent = list(_history[-100:])
        for ev in recent:
            await socket.send_json(ev)
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _clients.discard(socket)


@app.post("/event")
async def event(request: Request) -> dict[str, bool]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {"_raw": raw.decode("utf-8", errors="replace")[:2000]}

    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "data": data,
    }
    async with _lock:
        _history.append(record)
        if len(_history) > MAX_HISTORY:
            del _history[: len(_history) - MAX_HISTORY]

    dead: set[WebSocket] = set()
    for client in list(_clients):
        try:
            await client.send_json(record)
        except Exception:
            dead.add(client)
    for client in dead:
        _clients.discard(client)

    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
