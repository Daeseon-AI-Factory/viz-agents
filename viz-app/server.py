"""VIZ App — 통합 제품 (v0~v30 모든 기능 + MD 시각화 + 실시간 애니메이션).

기능 매핑:
  v0~v4:  Live HUD 기본 (events, NOW, LLM 요약, viz_kind)
  v5:     Python symbol diff
  v6:     /topology endpoint
  v7~v11: viz_kind (journey, arch, kpi, animation, whatif)
  v12:    Drill-down (클라이언트 더블클릭)
  v13:    Multi-agent (agent_id)
  v14:    Multi-pane (클라이언트)
  v15:    On-Demand /viz/request
  v16:    Multi-viewer (clients count)
  v17:    Mobile (클라이언트)
  v18:    Capture (클라이언트)
  v19:    /history (Time-Travel)
  v20:    /feedback
  v21:    우클릭 → 클립보드 (클라이언트)
  v22:    Webhook 알림
  v23:    화면 녹화 (클라이언트)
  v24:    /github/pr
  v25:    /code_quality (자동)
  v26:    /security (자동)
  v27:    /cost 트래커
  v28:    자동 회고 (12h)
  v29:    /favorite
  v30:    테마 (클라이언트)
  ★ NEW:  /docs — MD 파일 목록/내용 (실시간 watch)
  ★ NEW:  배경 파티클 애니메이션 (클라이언트)
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
PROJECT_ROOT = HERE.parent  # viz-agents/
LOCAL_KEY_PATH = HERE / ".local_key.txt"
FEEDBACK_PATH = HERE / ".feedback.jsonl"
FAVORITES_PATH = HERE / ".favorites.jsonl"

MAX_HISTORY = 2000
SUMMARY_MIN_INTERVAL_SEC = 25
SUMMARY_MAX_EVENTS = 30
PERIODIC_CHECK_SEC = 60
MIN_EVENTS_FOR_SUMMARY = 4
RETRO_INTERVAL_SEC = 12 * 3600
MD_POLL_SEC = 3

MODEL = "claude-haiku-4-5-20251001"
PRICE_IN_PER_M = 0.25
PRICE_OUT_PER_M = 1.25

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip()

SUMMARY_SYSTEM = """당신은 AI 어시스턴트(Claude Code)의 작업 시퀀스를 한국어로 분석합니다.

입력: 도구 호출 이벤트 리스트 (JSON).

출력 (반드시 다음 JSON 형식만, 다른 텍스트 절대 금지):

{
  "summary": "20-60자 한국어 한 줄 요약",
  "next_step": "0-30자 다음 할 일 추측",
  "files_touched": ["만진 파일 0-3개"],
  "viz_kind": "diff|table|gauge|flow|badge|code|animation|kpi|journey|arch|whatif|none",
  "viz_reason": "왜 그 viz_kind를 골랐는지 한 줄",
  "viz_data": { 그 viz_kind에 맞는 데이터 }
}

viz_kind 가이드:
  - diff      : 코드 변경 (Edit/Write). viz_data: {"file": "path", "before": "...", "after": "...", "lang": "python"}
  - table     : 여러 항목 비교/나열. {"headers": [...], "rows": [[...]]}
  - gauge     : 단일 수치. {"label": "...", "value": 12, "max": 15, "unit": "..."}
  - flow      : 순서 있는 단계. {"steps": [{"name": "...", "status": "done|now|todo"}]}
  - badge     : 단일 상태. {"label": "...", "tone": "success|error|warning|info"}
  - code      : 코드 스니펫. {"lang": "python", "code": "..."}
  - animation : 노드 사이 흐르는 애니메이션 (★ 비전 직격). {"nodes": [{"id":"...", "label":"..."}], "flow": ["id1","id2"], "duration_ms": 2500}
  - kpi       : 비즈니스 KPI 여러 메트릭. {"kpis": [{"label": "...", "value": "...", "trend": "up|down|flat", "delta": "..."}]}
  - journey   : 사용자 여정 단계. {"persona": "...", "stages": [{"name":"...", "icon":"...", "drop": 0}]}
  - arch      : 아키텍처 레이어. {"layers": [{"name": "Frontend", "components": ["..."]}], "active_layer": "..."}
  - whatif    : 현재 vs 변경 후. {"title": "...", "current": [{"k":"...","v":"..."}], "after": [{"k":"...","v":"...","change":"good|bad|neutral"}], "recommendation": "..."}
  - none      : 시각화 불필요

규칙:
- 같은 도구라도 작업 내용에 따라 다른 viz_kind 선택
- 흐름 성격 작업은 animation 우선 (정적 flow X)
- 코드 변화 = diff, 비즈니스 변화 = kpi, 시스템 변화 = arch
- JSON 외 다른 텍스트, 코드펜스 절대 금지
"""

app = FastAPI(title="VIZ App — Integrated Live HUD", docs_url=None, redoc_url=None, openapi_url=None)
_clients: set[WebSocket] = set()
_history: list[dict[str, Any]] = []
_lock = asyncio.Lock()
_last_summary_at: dict[str, float] = {}
_session_events: dict[str, list[dict]] = {}
_api_key: str = ""
_api_key_lock = asyncio.Lock()
_usage_in = 0
_usage_out = 0
_usage_calls = 0
_last_retro_at = 0.0
_md_mtimes: dict[str, float] = {}


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


# 키 로드 (디스크 → env 순)
_api_key = _load_key_from_disk() or os.environ.get("ANTHROPIC_API_KEY", "").strip()
# 다른 v* 폴더의 키 자동 복사
if not _api_key:
    for v in ["v20", "v19", "v15", "v10", "v4", "v3", "v2"]:
        p = PROJECT_ROOT / v / ".local_key.txt"
        if p.exists():
            try:
                _api_key = p.read_text(encoding="utf-8").strip()
                if _api_key:
                    _save_key_to_disk(_api_key)
                    break
            except Exception:
                pass


# ── V5: Python symbol diff ──
import re as _re

def _extract_py_symbols(code: str) -> dict:
    funcs = _re.findall(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)', code, _re.MULTILINE)
    classes = _re.findall(r'^\s*class\s+(\w+)', code, _re.MULTILINE)
    imports = _re.findall(r'^\s*(?:from\s+(\S+)\s+)?import\s+([^\n]+)', code, _re.MULTILINE)
    return {
        "functions": {n: f"def {n}({s.strip()})" for n, s in funcs},
        "classes": classes,
        "imports": [f"from {f} import {i.strip()}" if f else f"import {i.strip()}" for f, i in imports],
    }


def _diff_py_symbols(old: str, new: str) -> dict:
    o = _extract_py_symbols(old or "")
    n = _extract_py_symbols(new or "")
    of, nf = o["functions"], n["functions"]
    oc, nc = set(o["classes"]), set(n["classes"])
    oi, ni = set(o["imports"]), set(n["imports"])
    return {
        "added_functions": [nf[k] for k in nf if k not in of],
        "removed_functions": [of[k] for k in of if k not in nf],
        "changed_signatures": [{"name": k, "before": of[k], "after": nf[k]}
                               for k in of if k in nf and of[k] != nf[k]],
        "added_classes": list(nc - oc),
        "removed_classes": list(oc - nc),
        "added_imports": list(ni - oi),
        "removed_imports": list(oi - ni),
    }


# ── V22: Webhook ──
async def _send_webhook(text: str) -> None:
    if not WEBHOOK_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(WEBHOOK_URL, json={"text": text})
    except Exception:
        pass


# ── V27: Cost tracker ──
def _add_usage(in_t: int, out_t: int):
    global _usage_in, _usage_out, _usage_calls
    _usage_in += int(in_t or 0)
    _usage_out += int(out_t or 0)
    _usage_calls += 1


def _current_cost() -> dict:
    cost = (_usage_in / 1_000_000) * PRICE_IN_PER_M + (_usage_out / 1_000_000) * PRICE_OUT_PER_M
    return {"calls": _usage_calls, "input_tokens": _usage_in,
            "output_tokens": _usage_out, "cost_usd": round(cost, 5)}


def _now_ts() -> float:
    return datetime.now().timestamp()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _compact_events(events: list[dict]) -> list[dict]:
    out: list[dict] = []
    for ev in events:
        d = ev.get("data", {})
        name = d.get("hook_event_name", "")
        if name in ("PreToolUse", "_summary", "_code_quality", "_security", "_retro", "_md_change"):
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
                if tn in ("Edit", "Write", "NotebookEdit"):
                    if "old_string" in inp:
                        item["old"] = (inp.get("old_string") or "")[:500]
                    if "new_string" in inp:
                        item["new"] = (inp.get("new_string") or "")[:500]
                    if "content" in inp:
                        item["content"] = (inp.get("content") or "")[:500]
                    # V5
                    fp = item.get("file", "")
                    if fp.endswith(".py"):
                        old_c = inp.get("old_string") or ""
                        new_c = inp.get("new_string") or inp.get("content") or ""
                        diff = _diff_py_symbols(old_c, new_c)
                        if any(diff.values()):
                            item["symbol_diff"] = diff
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
    return {"summary": summary, "next_step": "", "files_touched": files[:3],
            "viz_kind": "none", "viz_reason": "fallback", "viz_data": {}}


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
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": MODEL, "max_tokens": 800, "system": SUMMARY_SYSTEM,
                      "messages": [{"role": "user", "content": user_msg}]},
            )
        if resp.status_code != 200:
            return _rule_based_summary(compact, note=f"API {resp.status_code}")
        body = resp.json()
        u = body.get("usage", {}) or {}
        _add_usage(u.get("input_tokens", 0), u.get("output_tokens", 0))
        text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return _rule_based_summary(compact, note="JSON 파싱")
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
    if not compact or len(compact) < MIN_EVENTS_FOR_SUMMARY:
        return
    result = await _call_llm_summary(compact)
    if not result:
        return
    record = {
        "ts": _now_iso(),
        "data": {"hook_event_name": "_summary", "session_id": session_id,
                 "reason": reason, "event_count": len(compact),
                 "llm_used": bool(await _get_key()), **result},
    }
    async with _lock:
        _history.append(record)
    await _broadcast(record)
    if reason == "stop" and WEBHOOK_URL:
        await _send_webhook(f"[VIZ] {result.get('summary', '')}")


# ── V25: 자동 코드 품질 ──
async def _analyze_code_quality(event_data: dict) -> None:
    inp = event_data.get("tool_input", {}) or {}
    fp = inp.get("file_path", "")
    new_code = inp.get("new_string") or inp.get("content") or ""
    if not new_code or len(new_code) < 20:
        return
    key = await _get_key()
    if not key:
        return
    prompt = (f"코드 품질. 파일: {fp}\n변경:\n{new_code[:1500]}\n\n"
              f"JSON: {{\"score\": 1-10, \"reason\": \"한국어 30자\"}}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": MODEL, "max_tokens": 100,
                      "messages": [{"role": "user", "content": prompt}]},
            )
        if resp.status_code != 200:
            return
        u = resp.json().get("usage", {}) or {}
        _add_usage(u.get("input_tokens", 0), u.get("output_tokens", 0))
        text = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        parsed = json.loads(text)
        record = {"ts": _now_iso(), "data": {"hook_event_name": "_code_quality",
                  "session_id": event_data.get("session_id", ""), "file": fp,
                  "score": parsed.get("score", 0), "reason": parsed.get("reason", "")}}
        async with _lock:
            _history.append(record)
        await _broadcast(record)
    except Exception:
        pass


# ── V26: 자동 보안 체크 ──
async def _analyze_security(event_data: dict) -> None:
    inp = event_data.get("tool_input", {}) or {}
    fp = inp.get("file_path", "")
    new_code = inp.get("new_string") or inp.get("content") or ""
    if not new_code or len(new_code) < 20:
        return
    key = await _get_key()
    if not key:
        return
    prompt = (f"보안. 파일: {fp}\n코드:\n{new_code[:1500]}\n\n"
              f"SQL injection/XSS/비밀 노출/위험 함수 체크.\n"
              f"JSON: {{\"severity\": \"none|low|medium|high|critical\", \"issues\": [\"한국어 50자\"]}}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": MODEL, "max_tokens": 200,
                      "messages": [{"role": "user", "content": prompt}]},
            )
        if resp.status_code != 200:
            return
        u = resp.json().get("usage", {}) or {}
        _add_usage(u.get("input_tokens", 0), u.get("output_tokens", 0))
        text = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        parsed = json.loads(text)
        if parsed.get("severity", "none") == "none":
            return
        record = {"ts": _now_iso(), "data": {"hook_event_name": "_security",
                  "session_id": event_data.get("session_id", ""), "file": fp,
                  "severity": parsed.get("severity", "low"),
                  "issues": parsed.get("issues", [])}}
        async with _lock:
            _history.append(record)
        await _broadcast(record)
    except Exception:
        pass


# ── 엔드포인트 ──
@app.get("/")
async def index() -> FileResponse:
    return FileResponse(HERE / "index.html")


@app.get("/healthz")
async def health() -> dict[str, Any]:
    key = await _get_key()
    return {
        "ok": True, "version": "app",
        "clients": len(_clients), "events": len(_history),
        "llm_enabled": bool(key), "model": MODEL if key else None,
        "key_source": _key_source(),
        "cost": _current_cost(),
        "webhook_set": bool(WEBHOOK_URL),
    }


@app.get("/key/status")
async def key_status() -> dict[str, Any]:
    key = await _get_key()
    return {"configured": bool(key),
            "preview": (key[:12] + "…" + key[-4:]) if key else "",
            "length": len(key), "source": _key_source()}


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
        return {"ok": True, "configured": False}
    if not new_key.startswith("sk-ant-"):
        return {"ok": False, "error": "키 형식 잘못됨"}
    if len(new_key) < 50:
        return {"ok": False, "error": f"키 짧음 ({len(new_key)})"}
    _save_key_to_disk(new_key)
    async with _api_key_lock:
        _api_key = new_key
    return {"ok": True, "configured": True, "length": len(new_key),
            "preview": new_key[:12] + "…" + new_key[-4:]}


@app.post("/key/test")
async def test_key() -> dict[str, Any]:
    key = await _get_key()
    if not key:
        return {"ok": False, "error": "키 없음"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": MODEL, "max_tokens": 5,
                      "messages": [{"role": "user", "content": "hi"}]},
            )
        if resp.status_code == 200:
            return {"ok": True, "status": 200}
        return {"ok": False, "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


# ── V6: Topology ──
@app.get("/topology")
async def topology() -> dict[str, Any]:
    touched: set[str] = set()
    async with _lock:
        for ev in _history[-300:]:
            d = ev.get("data", {})
            if d.get("hook_event_name") != "PostToolUse":
                continue
            tn = d.get("tool_name", "")
            if tn not in ("Read", "Edit", "Write", "NotebookEdit"):
                continue
            fp = (d.get("tool_input") or {}).get("file_path", "")
            if fp.endswith(".py"):
                touched.add(fp)
    nodes = []
    edges = []
    name_to_id = {}
    for fp in sorted(touched):
        try:
            short = Path(fp).name
            mod_id = Path(fp).stem
            name_to_id[mod_id] = mod_id
            nodes.append({"id": mod_id, "label": short, "path": fp})
        except Exception:
            pass
    for fp in touched:
        try:
            content = Path(fp).read_text(encoding="utf-8", errors="ignore")
            imports = _re.findall(r'^\s*(?:from\s+(\S+)\s+)?import\s+([^\n]+)', content, _re.MULTILINE)
            src = Path(fp).stem
            for from_pkg, imp in imports:
                target = (from_pkg or imp.split(",")[0]).strip().split(".")[0]
                if target in name_to_id and target != src:
                    edges.append({"from": src, "to": target})
        except Exception:
            pass
    return {"nodes": nodes, "edges": edges,
            "node_count": len(nodes), "edge_count": len(edges)}


# ── V19: History (Time-Travel) ──
@app.get("/history")
async def history(limit: int = 500) -> dict[str, Any]:
    async with _lock:
        events = list(_history[-limit:])
    if not events:
        return {"events": [], "first": None, "last": None, "total": 0}
    return {"events": events, "first": events[0]["ts"],
            "last": events[-1]["ts"], "total": len(events)}


# ── V20: Feedback ──
def _feedback_count() -> int:
    if not FEEDBACK_PATH.exists():
        return 0
    try:
        return sum(1 for _ in FEEDBACK_PATH.open(encoding="utf-8"))
    except Exception:
        return 0


@app.post("/feedback")
async def feedback(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False}
    record = {"ts": _now_iso(), "viz_kind": data.get("viz_kind", ""),
              "summary": data.get("summary", ""), "vote": data.get("vote", "")}
    if record["vote"] not in ("up", "down"):
        return {"ok": False}
    try:
        with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return {"ok": True, "total": _feedback_count()}


# ── V27: Cost ──
@app.get("/cost")
async def cost() -> dict[str, Any]:
    return _current_cost()


# ── V29: Favorites ──
@app.post("/favorite")
async def add_favorite(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False}
    record = {"ts": _now_iso(), "title": data.get("title", ""),
              "viz_kind": data.get("viz_kind", ""), "summary": data.get("summary", ""),
              "data": data.get("data", {})}
    try:
        with FAVORITES_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        return {"ok": False}
    return {"ok": True}


@app.get("/favorites")
async def list_favorites(limit: int = 50) -> dict[str, Any]:
    if not FAVORITES_PATH.exists():
        return {"favorites": []}
    try:
        lines = FAVORITES_PATH.read_text(encoding="utf-8").strip().split("\n")
        items = [json.loads(l) for l in lines[-limit:] if l.strip()]
        return {"favorites": items, "total": len(lines)}
    except Exception:
        return {"favorites": []}


# ── V15: On-Demand Viz Request ──
@app.post("/viz/request")
async def viz_request(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    user_req = (data.get("request") or "").strip()
    if not user_req:
        return {"ok": False, "error": "request 필드"}
    key = await _get_key()
    if not key:
        return {"ok": False, "error": "LLM 비활성"}
    async with _lock:
        recent = list(_history[-30:])
    compact = _compact_events(recent)
    user_msg = (f"사용자 요청: {user_req}\n\n참고 활동:\n"
                + json.dumps(compact[-10:], ensure_ascii=False))
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": MODEL, "max_tokens": 800, "system": SUMMARY_SYSTEM,
                      "messages": [{"role": "user", "content": user_msg}]},
            )
        if resp.status_code != 200:
            return {"ok": False, "error": f"API {resp.status_code}"}
        body = resp.json()
        u = body.get("usage", {}) or {}
        _add_usage(u.get("input_tokens", 0), u.get("output_tokens", 0))
        text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        parsed = json.loads(text)
        record = {"ts": _now_iso(), "data": {
            "hook_event_name": "_summary", "session_id": "_user_request",
            "reason": "on_demand", "event_count": 0, "llm_used": True,
            "request": user_req, **parsed}}
        async with _lock:
            _history.append(record)
        await _broadcast(record)
        return {"ok": True, "viz": parsed}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ── V24: GitHub PR ──
@app.post("/github/pr")
async def github_pr(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    pr_url = (data.get("url") or "").strip()
    m = _re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        return {"ok": False, "error": "GitHub PR URL 형식 X"}
    owner, repo, num = m.groups()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}",
                headers={"Accept": "application/vnd.github.v3+json"})
        if r.status_code != 200:
            return {"ok": False, "error": f"GitHub {r.status_code}"}
        pr_data = r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    key = await _get_key()
    if not key:
        return {"ok": False, "error": "LLM 비활성"}
    user_msg = (f"GitHub PR:\n제목: {pr_data.get('title', '')}\n"
                f"설명: {(pr_data.get('body') or '')[:1000]}\n"
                f"+{pr_data.get('additions', 0)} / -{pr_data.get('deletions', 0)} 줄, "
                f"{pr_data.get('changed_files', 0)} 파일")
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": MODEL, "max_tokens": 600, "system": SUMMARY_SYSTEM,
                      "messages": [{"role": "user", "content": user_msg}]})
        if resp.status_code != 200:
            return {"ok": False}
        u = resp.json().get("usage", {}) or {}
        _add_usage(u.get("input_tokens", 0), u.get("output_tokens", 0))
        text = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        parsed = json.loads(text)
        record = {"ts": _now_iso(), "data": {
            "hook_event_name": "_summary", "session_id": f"_gh_{owner}_{repo}_{num}",
            "reason": "github_pr", "event_count": 0, "llm_used": True,
            "pr_url": pr_url, "pr_title": pr_data.get("title", ""), **parsed}}
        async with _lock:
            _history.append(record)
        await _broadcast(record)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ── ★★ 자기참조 시각화: viz-app 자체의 시스템/비즈니스/제품 흐름 ──
@app.get("/system/flow")
async def system_flow() -> dict[str, Any]:
    """viz-app 자체의 시스템 데이터 흐름 (자기참조)"""
    return {
        "title": "🏛 viz-app 시스템 흐름",
        "nodes": [
            {"id": "user", "label": "사용자", "icon": "👤", "tone": "actor"},
            {"id": "claude", "label": "Claude Code", "icon": "🤖", "tone": "ai"},
            {"id": "hooks", "label": "Hooks", "icon": "🪝", "tone": "system"},
            {"id": "server", "label": "FastAPI", "icon": "⚙️", "tone": "core"},
            {"id": "llm", "label": "Anthropic LLM", "icon": "🧠", "tone": "external"},
            {"id": "ws", "label": "WebSocket", "icon": "📡", "tone": "system"},
            {"id": "browser", "label": "브라우저 HUD", "icon": "🖥", "tone": "ui"},
            {"id": "md", "label": "MD 파일", "icon": "📄", "tone": "data"},
            {"id": "disk", "label": "디스크", "icon": "💾", "tone": "data"},
        ],
        "edges": [
            {"from": "user", "to": "claude", "label": "요청"},
            {"from": "claude", "to": "hooks", "label": "tool 호출"},
            {"from": "hooks", "to": "server", "label": "POST /event"},
            {"from": "server", "to": "llm", "label": "요약·viz_kind 요청"},
            {"from": "llm", "to": "server", "label": "JSON 응답"},
            {"from": "server", "to": "ws", "label": "broadcast"},
            {"from": "ws", "to": "browser", "label": "실시간 push"},
            {"from": "browser", "to": "user", "label": "시각화"},
            {"from": "md", "to": "server", "label": "watcher 3s"},
            {"from": "server", "to": "disk", "label": "key/feedback/fav"},
        ],
        "flows": [
            {"name": "Claude 작업 흐름", "path": ["user", "claude", "hooks", "server", "llm", "server", "ws", "browser"], "color": "#58a6ff"},
            {"name": "MD 변경 흐름", "path": ["md", "server", "ws", "browser"], "color": "#3fb950"},
            {"name": "자연어 요청 흐름", "path": ["user", "browser", "server", "llm", "server", "ws", "browser"], "color": "#d29922"},
        ],
    }


@app.get("/system/business")
async def system_business() -> dict[str, Any]:
    """비즈니스 가치 흐름"""
    return {
        "title": "💎 비즈니스 가치 흐름",
        "persona": "비-엔지니어 / 영어 약함 / 집중력 짧음 사용자",
        "stages": [
            {"name": "텍스트 부담", "icon": "📚", "before": "AI 응답 wall of text"},
            {"name": "Hook 자동 캡처", "icon": "🪝", "value": "Claude 모든 액션 자동"},
            {"name": "LLM 압축", "icon": "🧠", "value": "한국어 한 줄 요약"},
            {"name": "시각 자동 선택", "icon": "🎨", "value": "11종 viz_kind 중 적합"},
            {"name": "동적 렌더", "icon": "✨", "value": "diff/KPI/animation/...별"},
            {"name": "즉시 이해", "icon": "💡", "after": "텍스트 읽지 않고 0.5초"},
        ],
        "kpis": [
            {"label": "텍스트 부담", "before": "100%", "after": "10%", "trend": "down"},
            {"label": "이해 속도", "before": "분 단위", "after": "초 단위", "trend": "up"},
            {"label": "옵션 비교", "before": "텍스트 wall", "after": "시각 카드", "trend": "up"},
            {"label": "세션 추적", "before": "1개", "after": "다중", "trend": "up"},
        ],
    }


@app.get("/system/product")
async def system_product() -> dict[str, Any]:
    """31개 버전 진화 트리"""
    return {
        "title": "🌳 제품 진화 트리 (v0 → v30 → viz-app)",
        "branches": [
            {"v": "v0-v4", "name": "기본 HUD", "color": "#58a6ff",
             "items": ["카드 timeline", "선택지 시각화", "세션 색 구분", "NOW 박스", "LLM 활동 요약"]},
            {"v": "v5-v11", "name": "viz_kind 컴포넌트", "color": "#3fb950",
             "items": ["symbol diff", "topology", "journey", "arch", "kpi", "★ animation", "whatif"]},
            {"v": "v12-v20", "name": "UX 트랙", "color": "#d29922",
             "items": ["drill-down", "multi-agent", "multi-pane", "on-demand", "viewer", "mobile", "capture", "time-travel", "feedback"]},
            {"v": "v21-v30", "name": "도구 트랙", "color": "#a371f7",
             "items": ["우클릭→클립", "webhook", "녹화", "GitHub PR", "코드품질", "보안", "비용", "회고", "즐겨찾기", "테마"]},
            {"v": "viz-app", "name": "통합 ★", "color": "#f78166",
             "items": ["전체 통합", "MD watcher", "배경 파티클", "3-탭 사이드바", "자기참조 시각"]},
        ],
        "total_versions": 31,
        "total_files": 186,
    }


# ── ★ MD 파일 시각화 ──
@app.get("/docs")
async def list_docs() -> dict[str, Any]:
    docs = []
    for md in sorted(PROJECT_ROOT.glob("*.md")):
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
            title = ""
            for line in content.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            docs.append({
                "name": md.name,
                "title": title or md.stem,
                "size": md.stat().st_size,
                "mtime": md.stat().st_mtime,
            })
        except Exception:
            pass
    return {"docs": docs, "count": len(docs)}


@app.get("/docs/{name}")
async def get_doc(name: str) -> dict[str, Any]:
    # 안전 — 파일명 정규화 (../ 차단)
    safe_name = Path(name).name
    md = PROJECT_ROOT / safe_name
    if not md.exists() or not md.suffix == ".md":
        return {"error": "not found", "name": safe_name}
    try:
        return {"name": safe_name, "content": md.read_text(encoding="utf-8", errors="ignore")}
    except Exception as e:
        return {"error": str(e)[:200]}


# ── ★ NEW: MD watcher (변경시 broadcast) ──
async def _md_watcher_loop() -> None:
    global _md_mtimes
    for md in PROJECT_ROOT.glob("*.md"):
        try:
            _md_mtimes[md.name] = md.stat().st_mtime
        except Exception:
            pass
    while True:
        await asyncio.sleep(MD_POLL_SEC)
        try:
            for md in PROJECT_ROOT.glob("*.md"):
                cur = md.stat().st_mtime
                prev = _md_mtimes.get(md.name)
                if prev is None or cur > prev:
                    _md_mtimes[md.name] = cur
                    record = {"ts": _now_iso(), "data": {
                        "hook_event_name": "_md_change",
                        "name": md.name,
                        "mtime": cur,
                    }}
                    async with _lock:
                        _history.append(record)
                    await _broadcast(record)
        except Exception:
            pass


# ── WebSocket ──
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


# ── 이벤트 수신 (hooks) ──
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
    # V25 + V26 자동 분석 (Edit/Write 시)
    if name == "PostToolUse" and isinstance(data, dict):
        tn = data.get("tool_name", "")
        if tn in ("Edit", "Write", "NotebookEdit"):
            asyncio.create_task(_analyze_code_quality(data))
            asyncio.create_task(_analyze_security(data))
    return {"ok": True}


# ── 백그라운드 루프 ──
async def _periodic_summary_loop() -> None:
    while True:
        await asyncio.sleep(PERIODIC_CHECK_SEC)
        for sid in list(_session_events.keys()):
            if _session_events.get(sid):
                try:
                    await _try_summarize(sid, "periodic")
                except Exception:
                    pass


async def _daily_retro_loop() -> None:
    global _last_retro_at
    while True:
        await asyncio.sleep(3600)
        now = _now_ts()
        if now - _last_retro_at < RETRO_INTERVAL_SEC:
            continue
        _last_retro_at = now
        key = await _get_key()
        if not key:
            continue
        async with _lock:
            events = list(_history[-300:])
        compact = _compact_events(events)
        if len(compact) < 5:
            continue
        prompt = (f"지난 12시간 활동 회고:\n{json.dumps(compact, ensure_ascii=False)[:3000]}\n\n"
                  f"JSON: {{\"summary\": \"3-5문장\", \"highlights\": [\"잘된 것\"], \"next\": \"내일\"}}")
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": MODEL, "max_tokens": 600,
                          "messages": [{"role": "user", "content": prompt}]})
            if resp.status_code != 200:
                continue
            u = resp.json().get("usage", {}) or {}
            _add_usage(u.get("input_tokens", 0), u.get("output_tokens", 0))
            text = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:].strip()
            parsed = json.loads(text)
            record = {"ts": _now_iso(), "data": {
                "hook_event_name": "_retro", "session_id": "_daily_retro", **parsed}}
            async with _lock:
                _history.append(record)
            await _broadcast(record)
        except Exception:
            pass


@app.on_event("startup")
async def _on_startup() -> None:
    asyncio.create_task(_periodic_summary_loop())
    asyncio.create_task(_daily_retro_loop())
    asyncio.create_task(_md_watcher_loop())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
