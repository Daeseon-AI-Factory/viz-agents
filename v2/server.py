"""VIZ V2 — Claude Code Live HUD with LLM activity summary.

V1 백엔드 + 백그라운드 요약 + 동적 API 키 관리.
- 매 Stop 이벤트마다 LLM 요약 → _summary 이벤트 broadcast
- 60초마다 미요약 세션 있으면 강제 요약
- 키 우선순위: .local_key.txt (있으면) > ANTHROPIC_API_KEY 환경변수
- POST /key 로 브라우저에서 키 입력/변경 가능
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

HERE = Path(__file__).parent
LOCAL_KEY_PATH = HERE / ".local_key.txt"
MAX_HISTORY = 1000
SUMMARY_MIN_INTERVAL_SEC = 25
SUMMARY_MAX_EVENTS = 30
PERIODIC_CHECK_SEC = 60
MIN_EVENTS_FOR_SUMMARY = 4  # 1-2 events 짜리는 요약 안 함 (노이즈 방지)

MODEL = "claude-haiku-4-5-20251001"
SUMMARY_SYSTEM = (
    "당신은 AI 어시스턴트(Claude Code)가 한 작업을 매우 간결한 한국어로 요약합니다.\n"
    "입력은 도구 호출 이벤트 리스트(JSON). 출력은 다음 JSON 형식만:\n"
    '{"summary":"한 줄(20-60자) 무엇을 했는지","next_step":"다음 할 일 추측 (0-30자)",'
    '"files_touched":["만진 파일 0-3개"]}\n'
    "JSON 외 다른 텍스트 절대 금지. 코드펜스 금지."
)

app = FastAPI(title="VIZ V2 Live HUD")
_clients: set[WebSocket] = set()
_history: list[dict[str, Any]] = []
_lock = asyncio.Lock()
_last_summary_at: dict[str, float] = {}
_session_events: dict[str, list[dict]] = {}
_api_key: str = ""
_api_key_lock = asyncio.Lock()


def _load_key_from_disk() -> str:
    if LOCAL_KEY_PATH.exists():
        try:
            return LOCAL_KEY_PATH.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""


def _save_key_to_disk(key: str) -> None:
    LOCAL_KEY_PATH.write_text(key, encoding="utf-8")
    try:
        os.chmod(LOCAL_KEY_PATH, 0o600)
    except Exception:
        pass


def _delete_key_from_disk() -> None:
    if LOCAL_KEY_PATH.exists():
        try:
            LOCAL_KEY_PATH.unlink()
        except Exception:
            pass


def _key_source() -> str:
    if LOCAL_KEY_PATH.exists():
        return "disk"
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return "env"
    return "none"


# 시작 시 키 로드 (디스크 우선, 환경변수 fallback)
_api_key = _load_key_from_disk() or os.environ.get("ANTHROPIC_API_KEY", "").strip()


def _now_ts() -> float:
    return datetime.now().timestamp()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _compact_events(events: list[dict]) -> list[dict]:
    out: list[dict] = []
    for ev in events:
        d = ev.get("data", {})
        name = d.get("hook_event_name", "")
        if name in ("PreToolUse", "_summary"):
            continue
        item: dict[str, Any] = {"event": name}
        if name == "UserPromptSubmit":
            item["prompt"] = (d.get("prompt") or "")[:400]
        elif name == "PostToolUse":
            tn = d.get("tool_name", "")
            inp = d.get("tool_input", {}) or {}
            item["tool"] = tn
            if tn in ("Read", "Edit", "Write", "NotebookEdit"):
                item["file"] = inp.get("file_path", "")
            elif tn == "Bash":
                item["cmd"] = (inp.get("command") or "")[:200]
                item["desc"] = inp.get("description", "")
            elif tn == "Grep":
                item["pattern"] = inp.get("pattern", "")
            elif tn == "Glob":
                item["glob"] = inp.get("pattern", "")
            elif tn in ("Agent", "Task"):
                item["agent"] = inp.get("subagent_type", "")
                item["desc"] = inp.get("description", "")
            elif tn == "AskUserQuestion":
                qs = inp.get("questions", []) or []
                item["question"] = (qs[0].get("question", "") if qs else "")[:200]
            else:
                item["input"] = json.dumps(inp, ensure_ascii=False)[:200]
        out.append(item)
    return out


def _rule_based_summary(compact: list[dict], note: str = "") -> dict:
    tool_counts: dict[str, int] = {}
    files: list[str] = []
    for ev in compact:
        t = ev.get("tool", "")
        if t:
            tool_counts[t] = tool_counts.get(t, 0) + 1
        f = ev.get("file", "")
        if f and f not in files:
            files.append(f)
    parts = [f"{n}× {t}" for t, n in sorted(tool_counts.items(), key=lambda x: -x[1])][:4]
    summary = ", ".join(parts) if parts else "활동 없음"
    if note:
        summary += f" ({note})"
    return {
        "summary": summary,
        "next_step": "",
        "files_touched": files[:3],
    }


async def _get_key() -> str:
    async with _api_key_lock:
        return _api_key


async def _call_llm_summary(compact: list[dict]) -> dict:
    if not compact:
        return {}
    key = await _get_key()
    if not key:
        return _rule_based_summary(compact, note="LLM 비활성")

    user_msg = "다음 이벤트들을 요약하세요:\n" + json.dumps(compact, ensure_ascii=False)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 400,
                    "system": SUMMARY_SYSTEM,
                    "messages": [{"role": "user", "content": user_msg}],
                },
            )
        if resp.status_code != 200:
            return _rule_based_summary(compact, note=f"API {resp.status_code}")
        body = resp.json()
        blocks = body.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return _rule_based_summary(compact, note="JSON 파싱 실패")
    except Exception as e:
        return _rule_based_summary(compact, note=f"err: {str(e)[:60]}")


async def _broadcast(record: dict) -> None:
    dead: set[WebSocket] = set()
    for c in list(_clients):
        try:
            await c.send_json(record)
        except Exception:
            dead.add(c)
    for c in dead:
        _clients.discard(c)


async def _try_summarize(session_id: str, reason: str) -> None:
    if not session_id:
        return
    pending = _session_events.get(session_id, [])
    if not pending:
        return
    now = _now_ts()
    if reason != "stop" and now - _last_summary_at.get(session_id, 0) < SUMMARY_MIN_INTERVAL_SEC:
        return

    events = list(pending)
    _session_events[session_id] = []
    _last_summary_at[session_id] = now

    compact = _compact_events(events)
    if not compact:
        return

    # 노이즈 방지: 너무 적은 이벤트는 요약 스킵
    if len(compact) < MIN_EVENTS_FOR_SUMMARY:
        return

    result = await _call_llm_summary(compact)
    if not result:
        return

    record = {
        "ts": _now_iso(),
        "data": {
            "hook_event_name": "_summary",
            "session_id": session_id,
            "reason": reason,
            "event_count": len(compact),
            "llm_used": bool(await _get_key()),
            **result,
        },
    }
    async with _lock:
        _history.append(record)
    await _broadcast(record)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(HERE / "index.html")


@app.get("/healthz")
async def health() -> dict[str, Any]:
    key = await _get_key()
    return {
        "ok": True,
        "version": "v2",
        "clients": len(_clients),
        "events": len(_history),
        "llm_enabled": bool(key),
        "model": MODEL if key else None,
        "key_source": _key_source(),
    }


@app.get("/key/status")
async def key_status() -> dict[str, Any]:
    key = await _get_key()
    return {
        "configured": bool(key),
        "preview": (key[:12] + "…" + key[-4:]) if key else "",
        "length": len(key),
        "source": _key_source(),
    }


@app.post("/key")
async def set_key(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}
    new_key = (data.get("key") or "").strip()

    if not new_key:
        global _api_key
        async with _api_key_lock:
            _api_key = ""
        _delete_key_from_disk()
        return {"ok": True, "configured": False, "message": "키 제거됨"}

    if not new_key.startswith("sk-ant-"):
        return {
            "ok": False,
            "error": "키 형식 잘못됨 — sk-ant- 로 시작해야 합니다",
        }
    if len(new_key) < 50:
        return {"ok": False, "error": f"키가 너무 짧음 ({len(new_key)}자)"}

    _save_key_to_disk(new_key)
    async with _api_key_lock:
        _api_key = new_key

    return {
        "ok": True,
        "configured": True,
        "length": len(new_key),
        "preview": new_key[:12] + "…" + new_key[-4:],
    }


@app.post("/key/test")
async def test_key() -> dict[str, Any]:
    key = await _get_key()
    if not key:
        return {"ok": False, "error": "키 없음"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
        if resp.status_code == 200:
            return {"ok": True, "status": 200}
        return {
            "ok": False,
            "status": resp.status_code,
            "error": resp.json().get("error", {}).get("message", "")[:200] if "application/json" in resp.headers.get("content-type", "") else "",
        }
    except Exception as e:
        return {"ok": False, "error": f"네트워크 에러: {str(e)[:120]}"}


@app.websocket("/ws")
async def ws(socket: WebSocket) -> None:
    await socket.accept()
    _clients.add(socket)
    try:
        async with _lock:
            recent = list(_history[-150:])
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

    record = {"ts": _now_iso(), "data": data}
    async with _lock:
        _history.append(record)
        if len(_history) > MAX_HISTORY:
            del _history[: len(_history) - MAX_HISTORY]

    await _broadcast(record)

    sid = data.get("session_id", "") if isinstance(data, dict) else ""
    name = data.get("hook_event_name", "") if isinstance(data, dict) else ""
    if sid and name and name != "PreToolUse":
        _session_events.setdefault(sid, []).append(record)
        if name == "Stop":
            asyncio.create_task(_try_summarize(sid, "stop"))
        elif len(_session_events[sid]) >= SUMMARY_MAX_EVENTS:
            asyncio.create_task(_try_summarize(sid, "max_events"))

    return {"ok": True}


async def _periodic_summary_loop() -> None:
    while True:
        await asyncio.sleep(PERIODIC_CHECK_SEC)
        for sid in list(_session_events.keys()):
            if _session_events.get(sid):
                try:
                    await _try_summarize(sid, "periodic")
                except Exception:
                    pass


@app.on_event("startup")
async def _on_startup() -> None:
    asyncio.create_task(_periodic_summary_loop())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
