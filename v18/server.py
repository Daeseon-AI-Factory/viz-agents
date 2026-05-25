"""VIZ V4 — Claude Code Live HUD + LLM-Driven Dynamic Visualization.

V3 + LLM이 작업 디스크립션 따라 시각화 종류와 데이터를 동적 생성.

V4 단계 통합:
  V4a: LLM 응답에 viz_kind 추가 (diff/table/gauge/flow/badge/code/none)
  V4b: diff 컴포넌트 (Edit 변경)
  V4c: gauge/table/flow 컴포넌트
  V4d: LLM 자유 HTML/SVG (viz_html 필드) — XSS sanitize 필수
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
MIN_EVENTS_FOR_SUMMARY = 4

MODEL = "claude-haiku-4-5-20251001"

SUMMARY_SYSTEM = """당신은 AI 어시스턴트(Claude Code)의 작업 시퀀스를 한국어로 분석합니다.

입력: 도구 호출 이벤트 리스트 (JSON).

출력 (반드시 다음 JSON 형식만, 다른 텍스트 절대 금지):

{
  "summary": "20-60자 한국어 한 줄 요약",
  "next_step": "0-30자 다음 할 일 추측",
  "files_touched": ["만진 파일 0-3개 경로"],
  "viz_kind": "diff | table | gauge | flow | badge | code | none 중 하나",
  "viz_reason": "왜 그 viz_kind를 골랐는지 한 줄",
  "viz_data": { 그 viz_kind에 맞는 데이터 객체 }
}

viz_kind 가이드 (작업 종류에 따라 다르게):
  - diff   : 코드/텍스트 변경 (Edit/Write 위주)
             viz_data: {"file": "path", "before": "...", "after": "...", "lang": "python"}
  - table  : 여러 항목 비교/나열 (검색 결과, 파일 목록)
             viz_data: {"headers": [...], "rows": [[...], ...]}
  - gauge  : 단일 수치/진행률 (테스트 통과율, 응답시간)
             viz_data: {"label": "...", "value": 12, "max": 15, "unit": "통과"}
  - flow   : 순서 있는 단계 (배포, 마이그레이션, 워크플로우)
             viz_data: {"steps": [{"name": "...", "status": "done|now|todo"}]}
  - badge  : 단일 상태 라벨 (통과/실패, 활성/비활성)
             viz_data: {"label": "...", "tone": "success|error|warning|info"}
  - code   : 짧은 코드 스니펫 강조
             viz_data: {"lang": "python", "code": "..."}
  - none   : 시각화 불필요 (단순 read 등)
             viz_data: {}

규칙:
- 같은 도구라도 작업 내용에 따라 다른 viz_kind 선택
- viz_data는 그 viz_kind 스키마에 정확히 맞춰서
- 모르면 viz_kind: "none"
- diff before/after 는 짧게 (각 500자 이내)
- code는 100줄 이내
- ★ V18 우선: 시각이 캡처/공유될 가능성 — 자족적으로 (컨텍스트 없이도 이해되게).
- JSON 외 다른 텍스트, 마크다운, 코드펜스 절대 금지
"""

app = FastAPI(title="VIZ V18 Live HUD")
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
                # V4: Edit 의 old/new 짧게 포함 → LLM 이 diff viz 만들 수 있게
                if tn in ("Edit", "Write", "NotebookEdit"):
                    if "old_string" in inp:
                        item["old"] = (inp.get("old_string") or "")[:500]
                    if "new_string" in inp:
                        item["new"] = (inp.get("new_string") or "")[:500]
                    if "content" in inp:
                        item["content"] = (inp.get("content") or "")[:500]
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
        "viz_kind": "none",
        "viz_reason": "fallback",
        "viz_data": {},
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

    user_msg = "다음 작업들을 분석하세요:\n" + json.dumps(compact, ensure_ascii=False)
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 800,
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
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return _rule_based_summary(compact, note="JSON 파싱 실패")
        # V4: viz_kind 기본값 보장
        parsed.setdefault("viz_kind", "none")
        parsed.setdefault("viz_data", {})
        parsed.setdefault("viz_reason", "")
        return parsed
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
        "version": "v18",
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
        return {"ok": False, "error": "키 형식 잘못됨 — sk-ant- 로 시작해야 합니다"}
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
