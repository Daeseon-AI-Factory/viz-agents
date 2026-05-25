"""viz-core — AI 출력 시각화 R&D 레이어. 단순화 빌드.

핵심:
  - 입력: Hook 이벤트 / 자연어 요청 / 외부 POST (3가지만)
  - 출력: 11종 viz_kind 자동 매핑
  - 단일 책임: 렌더만

엔드포인트 (7개만):
  GET  /                 — index.html
  GET  /healthz          — 상태
  GET  /ws               — WebSocket (실시간 push)
  POST /event            — Hook 이벤트 수신
  GET  /history          — 과거 이벤트 (스크럽용, 옵션)
  POST /viz/request      — 자연어 시각 요청
  POST /favorite         — ⭐ 즐겨찾기
  GET  /key/status       — 키 상태
  POST /key              — 키 저장
  POST /key/test         — 키 작동 확인

(제거: /docs /topology /cost /github/pr /feedback /system/*
       자동 코드품질/보안 분석, 12h 회고, webhook)
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
PROJECT_ROOT = HERE.parent
LOCAL_KEY_PATH = HERE / ".local_key.txt"
FAVORITES_PATH = HERE / ".favorites.jsonl"

MAX_HISTORY = 500
SUMMARY_MIN_INTERVAL_SEC = 25
SUMMARY_MAX_EVENTS = 30
PERIODIC_CHECK_SEC = 60
MIN_EVENTS_FOR_SUMMARY = 4

MODEL = "claude-haiku-4-5-20251001"

SUMMARY_SYSTEM = """당신은 AI 어시스턴트(Claude Code)의 작업 시퀀스를 한국어로 분석합니다.

입력: 도구 호출 이벤트 리스트 (JSON).

출력 (반드시 다음 JSON 형식만, 다른 텍스트 절대 금지):

{
  "summary": "20-60자 한국어 한 줄",
  "next_step": "0-30자 다음 할 일",
  "files_touched": ["만진 파일 0-3개"],
  "viz_kind": "diff|table|gauge|flow|badge|code|animation|kpi|journey|arch|whatif|none",
  "viz_reason": "왜 그 viz_kind 골랐는지 한 줄",
  "viz_data": { 해당 viz_kind 스키마에 맞는 데이터 }
}

viz_kind 가이드:
  - diff      : 코드 변경. {"file","before","after","lang"}
  - table     : 여러 항목. {"headers","rows"}
  - gauge     : 단일 수치. {"label","value","max","unit"}
  - flow      : 순서 단계. {"steps":[{"name","status":"done|now|todo"}]}
  - badge     : 상태 라벨. {"label","tone":"success|error|warning|info"}
  - code      : 코드 스니펫. {"lang","code"}
  - animation : 흐름 애니메이션 ★. {"nodes":[{"id","label"}],"flow":[id...],"duration_ms"}
  - kpi       : 비즈니스 메트릭. {"kpis":[{"label","value","trend":"up|down|flat","delta"}]}
  - journey   : 사용자 여정. {"persona","stages":[{"name","icon","drop"}]}
  - arch      : 아키텍처 레이어. {"layers":[{"name","components":[...]}],"active_layer"}
  - whatif    : 영향 비교. {"title","current":[{"k","v"}],"after":[{"k","v","change":"good|bad|neutral"}],"recommendation"}
  - none      : 시각화 불필요

규칙:
- 같은 도구라도 작업 내용에 따라 다른 viz_kind 선택
- 흐름 성격은 animation 우선
- JSON 외 다른 텍스트 / 코드펜스 절대 금지
"""

app = FastAPI(title="viz-core", docs_url=None, redoc_url=None, openapi_url=None)
_clients: set[WebSocket] = set()
_history: list[dict[str, Any]] = []
_lock = asyncio.Lock()
_last_summary_at: dict[str, float] = {}
_session_events: dict[str, list[dict]] = {}
_api_key: str = ""
_api_key_lock = asyncio.Lock()


# ── 키 관리 ──
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


# 시작 시 키 로드 (디스크 → env → 이전 v* 폴더)
_api_key = _load_key_from_disk() or os.environ.get("ANTHROPIC_API_KEY", "").strip()
if not _api_key:
    for v in ["viz-app", "v30", "v20", "v15", "v10", "v4"]:
        p = PROJECT_ROOT / v / ".local_key.txt"
        if p.exists():
            try:
                _api_key = p.read_text(encoding="utf-8").strip()
                if _api_key:
                    _save_key_to_disk(_api_key)
                    break
            except Exception:
                pass


# ── 유틸 ──
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
    user_msg = "다음 작업들을 분석:\n" + json.dumps(compact, ensure_ascii=False)
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
    record = {"ts": _now_iso(), "data": {
        "hook_event_name": "_summary", "session_id": session_id,
        "reason": reason, "event_count": len(compact),
        "llm_used": bool(await _get_key()), **result}}
    async with _lock:
        _history.append(record)
    await _broadcast(record)


# ── 엔드포인트 (7개만) ──
@app.get("/")
async def index() -> FileResponse:
    return FileResponse(HERE / "index.html")


@app.get("/healthz")
async def health() -> dict[str, Any]:
    key = await _get_key()
    return {"ok": True, "version": "core",
            "clients": len(_clients), "events": len(_history),
            "llm_enabled": bool(key), "model": MODEL if key else None,
            "key_source": _key_source()}


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
        return {"ok": False, "error": "키는 sk-ant- 로 시작"}
    if len(new_key) < 50:
        return {"ok": False, "error": f"키 짧음 ({len(new_key)}자)"}
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
        return {"ok": resp.status_code == 200, "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


@app.get("/history")
async def history(limit: int = 200) -> dict[str, Any]:
    async with _lock:
        events = list(_history[-limit:])
    return {"events": events, "total": len(events),
            "first": events[0]["ts"] if events else None,
            "last": events[-1]["ts"] if events else None}


@app.post("/viz/request")
async def viz_request(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    user_req = (data.get("request") or "").strip()
    if not user_req:
        return {"ok": False, "error": "request 필드 비어있음"}
    key = await _get_key()
    if not key:
        return {"ok": False, "error": "LLM 비활성 — 키 설정 필요"}
    async with _lock:
        recent = list(_history[-30:])
    compact = _compact_events(recent)
    user_msg = (f"사용자 자연어 요청: {user_req}\n\n참고 활동:\n"
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
        text = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
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


# ── ★ 시각화 specialist 에이전트 (LLM 위임) ──
# 핵심: 자체 분석 X. Claude 에게 "이 입력을 viz_kind+viz_data 로" 위임.
# 자세히는 CORE.md 참고.

VIZ_AGENT_SYSTEM = """당신은 viz-core 의 시각화 specialist AI 에이전트입니다.

역할: 입력 (코드/문서/repo/자연어) 을 받아서, 사용자가 0.5초에 이해할 시각으로 변환.

출력 (반드시 JSON, 다른 텍스트 X):
{
  "summary": "20-60자 한국어",
  "next_step": "0-30자 다음 할 일",
  "viz_kind": "callgraph|diff|table|gauge|flow|badge|code|animation|kpi|journey|arch|whatif|none",
  "viz_reason": "왜 그 viz_kind 골랐는지 한 줄",
  "viz_data": { 그 viz_kind 스키마에 맞게 }
}

viz_kind 가이드 (입력 → 추천):
  - 코드 호출 그래프 → "callgraph" {nodes:[{id,label,in_degree,out_degree,entry_kind}], edges:[{from,to}], entries:[{entry,kind,chain}]}
  - 코드 변경 → "diff" {file, before, after, lang}
  - 단일 수치 → "gauge" {label, value, max, unit}
  - 여러 항목 → "table" {headers, rows}
  - 순서 단계 → "flow" {steps:[{name,status}]}
  - 단일 상태 → "badge" {label, tone}
  - 코드 스니펫 → "code" {lang, code}
  - 데이터 흐름 → "animation" {nodes:[{id,label}], flow:[id...], duration_ms}
  - 비즈니스 KPI → "kpi" {kpis:[{label,value,trend,delta}]}
  - 사용자 여정 → "journey" {persona, stages:[{name,icon,drop}]}
  - 시스템 아키텍처 → "arch" {layers:[{name, components}], active_layer}
  - 영향 비교 → "whatif" {title, current, after, recommendation}

규칙:
- 분석은 깊이 X. 시각화 specialist 로서 어떻게 보여줄지에만 집중.
- 코드면 callgraph, 시스템 설명이면 arch, 흐름이면 animation 우선.
- JSON 외 다른 텍스트, 코드펜스 절대 금지.
"""


async def _viz_agent_call(input_text: str, input_kind: str = "unknown") -> dict:
    """LLM 호출 — viz_kind+viz_data JSON 받음. 자체 분석 X, LLM 위임."""
    key = await _get_key()
    if not key:
        return {"summary": f"({input_kind}) 입력 받음, LLM 비활성", "viz_kind": "none", "viz_data": {}}
    user_msg = f"입력 종류: {input_kind}\n\n입력 내용:\n{input_text[:6000]}"
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": MODEL, "max_tokens": 1500, "system": VIZ_AGENT_SYSTEM,
                      "messages": [{"role": "user", "content": user_msg}]},
            )
        if resp.status_code != 200:
            return {"summary": f"LLM 에러 {resp.status_code}", "viz_kind": "badge",
                    "viz_data": {"label": f"API {resp.status_code}", "tone": "error"}}
        text = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {"summary": "LLM 응답 JSON 파싱 실패", "viz_kind": "code",
                    "viz_data": {"lang": "json", "code": text[:500]}}
        parsed.setdefault("viz_kind", "none")
        parsed.setdefault("viz_data", {})
        return parsed
    except Exception as e:
        return {"summary": f"에러: {str(e)[:80]}", "viz_kind": "badge",
                "viz_data": {"label": "에러", "tone": "error"}}


# ── (참고용) 옛 AST 분석 — viz-core 의 책임 X. 호환성을 위해 stub 으로 남김. ──
import ast as _ast


def _identify_entry_kind(node) -> str | None:
    """함수 데코레이터 보고 entry point 종류 판단"""
    decorators = getattr(node, "decorator_list", [])
    for dec in decorators:
        # @app.get("/path"), @app.post(...), @app.websocket(...)
        if isinstance(dec, _ast.Call):
            if isinstance(dec.func, _ast.Attribute):
                attr = dec.func.attr
                if attr in ("get", "post", "put", "delete", "patch"):
                    return f"http_{attr}"
                if attr == "websocket":
                    return "websocket"
                if attr == "on_event":
                    return "lifecycle"
                if attr in ("route", "task", "command"):
                    return attr
        elif isinstance(dec, _ast.Attribute):
            if dec.attr == "command":  # @click.command
                return "cli"
    # main 함수
    if node.name in ("main", "run", "handler", "lambda_handler"):
        return "main"
    return None


def _trace_calls_from(start: str, all_funcs: dict, depth: int = 4) -> list:
    """특정 함수에서 시작해서 호출 체인 추적 (BFS, depth 제한)"""
    visited = set()
    queue = [(start, 0)]
    chain = []
    while queue:
        node, d = queue.pop(0)
        if node in visited or d > depth:
            continue
        visited.add(node)
        chain.append(node)
        for callee in all_funcs.get(node, []):
            if callee not in visited:
                queue.append((callee, d + 1))
    return chain


def _analyze_python_file(path: str) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return {"error": f"파일 없음: {path}"}
    if p.suffix != ".py":
        return {"error": f".py 만 지원: {p.suffix}"}
    try:
        src = p.read_text(encoding="utf-8", errors="ignore")
        tree = _ast.parse(src, filename=str(p))
    except SyntaxError as e:
        return {"error": f"파싱 실패: {e}"}

    classes, functions, imports, calls = [], [], [], []
    entry_points = []  # ★ NEW

    for node in _ast.walk(tree):
        if isinstance(node, _ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno,
                            "methods": [n.name for n in node.body if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))]})
        elif isinstance(node, _ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, _ast.ImportFrom):
            mod = node.module or ""
            imports.append(mod)

    # top-level 함수 + entry 식별
    for node in tree.body:
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            kind = _identify_entry_kind(node)
            functions.append({"name": node.name, "line": node.lineno,
                              "args": args, "is_async": isinstance(node, _ast.AsyncFunctionDef),
                              "entry_kind": kind})
            if kind:
                entry_points.append({"name": node.name, "kind": kind, "line": node.lineno})

    # 호출 관계 추출 (caller → callee)
    callable_names = {f["name"] for f in functions}
    for c in classes:
        for m in c["methods"]:
            callable_names.add(m)

    func_calls = {}  # name → list of callees
    for node in tree.body:
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            caller = node.name
            callees = []
            for sub in _ast.walk(node):
                if isinstance(sub, _ast.Call):
                    callee = None
                    if isinstance(sub.func, _ast.Name):
                        callee = sub.func.id
                    elif isinstance(sub.func, _ast.Attribute):
                        callee = sub.func.attr
                    if callee and callee in callable_names and callee != caller:
                        calls.append({"from": caller, "to": callee})
                        if callee not in callees:
                            callees.append(callee)
            func_calls[caller] = callees

    # ★ 각 entry point 마다 호출 chain 추적
    entry_chains = []
    for ep in entry_points:
        chain = _trace_calls_from(ep["name"], func_calls)
        entry_chains.append({
            "entry": ep["name"],
            "kind": ep["kind"],
            "line": ep["line"],
            "chain": chain,
            "depth": len(chain),
        })

    return {
        "file": str(p), "name": p.name,
        "classes": classes, "functions": functions,
        "imports": sorted(set(imports))[:30], "calls": calls,
        "entry_points": entry_points,
        "entry_chains": entry_chains,
        "line_count": len(src.split("\n")),
    }


def _analyze_to_viz(analysis: dict) -> dict[str, Any]:
    if "error" in analysis:
        return {"summary": f"분석 실패: {analysis['error']}",
                "viz_kind": "badge",
                "viz_data": {"label": analysis["error"], "tone": "error"}}
    classes = analysis["classes"]
    functions = analysis["functions"]
    calls = analysis["calls"]
    if calls:
        # 그래프 추출: 모든 unique 노드 + 모든 edges
        node_ids = set()
        for c in calls:
            node_ids.add(c["from"])
            node_ids.add(c["to"])

        in_deg = {n: 0 for n in node_ids}
        out_deg = {n: 0 for n in node_ids}
        edge_set = set()
        for c in calls:
            key = (c["from"], c["to"])
            if key in edge_set:
                continue
            edge_set.add(key)
            in_deg[c["to"]] += 1
            out_deg[c["from"]] += 1

        # ★ entry point 노드는 별도 표시 (kind 메타데이터)
        entry_map = {ep["name"]: ep["kind"] for ep in analysis.get("entry_points", [])}
        nodes = [{"id": n, "label": n,
                  "in_degree": in_deg[n], "out_degree": out_deg[n],
                  "entry_kind": entry_map.get(n)}
                 for n in sorted(node_ids)]
        edges = [{"from": a, "to": b} for (a, b) in edge_set]

        # ★ entry_chains 도 같이 보냄 — 클라가 entry 별 sub-graph 시각 가능
        return {
            "summary": f"📦 {analysis['name']} — {len(analysis.get('entry_points', []))} entries, {len(functions)} fn, {len(edge_set)} calls",
            "next_step": f"{analysis['line_count']}줄",
            "files_touched": [analysis["file"]],
            "viz_kind": "callgraph",
            "viz_reason": f"진입점 {len(analysis.get('entry_points', []))}개, {len(node_ids)} 노드, {len(edge_set)} edge",
            "viz_data": {
                "nodes": nodes,
                "edges": edges,
                "entries": analysis.get("entry_chains", []),
                "duration_ms": 4000,
            }
        }
    if classes:
        return {
            "summary": f"📦 {analysis['name']} — {len(classes)} class, {len(functions)} fn",
            "files_touched": [analysis["file"]],
            "viz_kind": "arch",
            "viz_data": {
                "layers": [
                    {"name": f"Classes ({len(classes)})", "components": [c["name"] for c in classes[:8]]},
                    {"name": f"Functions ({len(functions)})", "components": [f["name"] for f in functions[:8]]},
                    {"name": "Imports", "components": analysis["imports"][:8]},
                ]
            }
        }
    return {
        "summary": f"📦 {analysis['name']} — {len(functions)} 함수",
        "files_touched": [analysis["file"]],
        "viz_kind": "table",
        "viz_data": {
            "headers": ["함수", "줄", "인자", "async"],
            "rows": [[f["name"], f["line"], ", ".join(f["args"]), "✓" if f.get("is_async") else ""] for f in functions[:20]],
        }
    }


# ── ★ NEW: 디렉토리 list (UI에서 파일 picker용) ──
@app.get("/list")
async def list_dir(path: str = "~") -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"ok": False, "error": "경로 없음"}
    if p.is_file():
        return {"ok": True, "type": "file", "path": str(p)}
    if not p.is_dir():
        return {"ok": False, "error": "지원 안 함"}
    items = []
    try:
        for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if child.name.startswith(".") and child.name not in (".env", ".gitignore"):
                continue
            items.append({
                "name": child.name,
                "path": str(child),
                "is_dir": child.is_dir(),
                "is_py": child.suffix == ".py" if not child.is_dir() else False,
            })
    except PermissionError:
        return {"ok": False, "error": "권한 없음"}
    return {"ok": True, "type": "dir", "path": str(p),
            "parent": str(p.parent) if p != p.parent else None,
            "items": items[:300]}


# ── ★ NEW: 업로드된 파일 직접 분석 (드래그앤드롭용) ──
@app.post("/analyze/upload")
async def analyze_upload(request: Request) -> dict[str, Any]:
    """업로드/드래그된 파일 내용 → LLM 시각화 에이전트에 위임. 어떤 언어든 OK."""
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    name = data.get("name", "uploaded.txt")
    content = data.get("content", "")
    if not content:
        return {"ok": False, "error": "content 비어있음"}

    # LLM specialist 에이전트 — 어떤 언어/형식이든 viz_kind 자동 선택
    suffix = Path(name).suffix or "file"
    viz = await _viz_agent_call(content, input_kind=f"{suffix} ({name})")
    viz.setdefault("files_touched", [f"(uploaded) {name}"])
    record = {"ts": _now_iso(), "data": {
        "hook_event_name": "_summary", "session_id": "_upload",
        "reason": "uploaded_file", "event_count": 0,
        "llm_used": bool(await _get_key()),
        **viz}}
    async with _lock:
        _history.append(record)
    await _broadcast(record)
    return {"ok": True, "viz": viz}


# ── ★ NEW: repo 전체 시각화 (디렉토리 → tree 요약 → LLM 위임) ──
# ── Repo Analyzer 위임 (analyzers/repo.py 모듈) ──
from analyzers.repo import analyze_repo as _repo_analyze


@app.post("/analyze/repo")
async def analyze_repo(request: Request) -> dict[str, Any]:
    """로컬 경로 OR GitHub URL → analyzers/repo.py 위임 → viz JSON."""
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    target = (data.get("path") or data.get("url") or "").strip()
    if not target:
        return {"ok": False, "error": "path 또는 url 필드 비어있음"}

    # analyzers 모듈에 LLM 호출 함수를 콜백으로 주입 (DI)
    viz = await _repo_analyze(target, llm_call=_viz_agent_call)
    if viz.get("error"):
        return {"ok": False, "error": viz["error"]}

    # Step 1: 큰 그림 카드 broadcast
    deep = viz.pop("_deep", None)  # 분리해서 별도 broadcast
    record = {"ts": _now_iso(), "data": {
        "hook_event_name": "_summary", "session_id": "_repo_viz",
        "reason": "repo_viz_overview", "event_count": 0,
        "llm_used": bool(await _get_key()),
        **viz}}
    async with _lock:
        _history.append(record)
    await _broadcast(record)

    # Step 2: deep 분석 결과 각 파일마다 별도 카드 broadcast
    if deep and deep.get("analyses"):
        for a in deep["analyses"]:
            if "viz" not in a:
                continue
            fviz = a["viz"]
            fviz.setdefault("files_touched", [a.get("file", "")])
            fviz["summary"] = f"🔍 {a['file']} — " + (fviz.get("summary") or "")
            frecord = {"ts": _now_iso(), "data": {
                "hook_event_name": "_summary", "session_id": "_repo_viz",
                "reason": "repo_viz_deep", "event_count": 0,
                "llm_used": True,
                **fviz}}
            async with _lock:
                _history.append(frecord)
            await _broadcast(frecord)

    return {"ok": True, "viz": viz, "deep": deep, "target": target}


@app.post("/analyze/code")
async def analyze_code(request: Request) -> dict[str, Any]:
    """파일 경로 → 내용 읽어서 LLM 시각화 specialist 에이전트에 위임."""
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    path = (data.get("path") or "").strip()
    if not path:
        return {"ok": False, "error": "path 필드 비어있음"}
    p = Path(path).expanduser().resolve()
    if p.is_dir():
        # 디렉토리 → 첫 코드 파일 (단순화. 향후 repo 전체 분석)
        cands = list(p.glob("*.py")) + list(p.glob("*.ts")) + list(p.glob("*.js")) + list(p.glob("*.go"))
        if not cands:
            return {"ok": False, "error": "디렉토리에 코드 없음"}
        p = cands[0]
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

    # LLM specialist 에이전트에 위임 (자체 분석 X)
    input_kind = f"{p.suffix or 'file'} ({p.name})"
    viz = await _viz_agent_call(content, input_kind=input_kind)
    viz.setdefault("files_touched", [str(p)])
    record = {"ts": _now_iso(), "data": {
        "hook_event_name": "_summary", "session_id": "_viz_agent",
        "reason": "code_viz", "event_count": 0,
        "llm_used": bool(await _get_key()),
        **viz}}
    async with _lock:
        _history.append(record)
    await _broadcast(record)
    return {"ok": True, "viz": viz, "file": str(p)}


@app.post("/favorite")
async def add_favorite(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False}
    record = {"ts": _now_iso(),
              "title": data.get("title", ""),
              "viz_kind": data.get("viz_kind", ""),
              "summary": data.get("summary", ""),
              "data": data.get("data", {})}
    try:
        with FAVORITES_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        return {"ok": False}
    return {"ok": True}


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


# ── ★ NEW: 파일 watcher (저장 시 자동 분석) ──
_watch_targets: dict[str, dict] = {}  # path → {mtimes, last_analyzed_at, paused}
_watch_task: asyncio.Task | None = None
WATCH_DEBOUNCE_SEC = 5  # 같은 파일 5초 안 재분석 X
WATCH_POLL_SEC = 2
WATCH_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".md"}
WATCH_SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", ".next"}


def _scan_mtimes(root: Path, max_files: int = 500) -> dict[str, float]:
    """root 하위 모든 코드 파일 mtime 매핑"""
    result = {}
    count = 0
    for p in root.rglob("*"):
        if count >= max_files:
            break
        if any(part in WATCH_SKIP_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in WATCH_EXTS:
            try:
                result[str(p)] = p.stat().st_mtime
                count += 1
            except Exception:
                pass
    return result


async def _watcher_loop() -> None:
    """모든 watch 타겟의 파일 변경 감지 → 자동 분석"""
    while True:
        await asyncio.sleep(WATCH_POLL_SEC)
        for root_path, state in list(_watch_targets.items()):
            if state.get("paused"):
                continue
            root = Path(root_path)
            if not root.exists() or not root.is_dir():
                continue
            try:
                current = _scan_mtimes(root)
                old = state.get("mtimes", {})
                changed = []
                for fp, mt in current.items():
                    if old.get(fp) != mt:
                        changed.append(fp)
                state["mtimes"] = current
                if not changed:
                    continue
                # 디바운스 — 같은 파일 5초 안 재분석 X
                last = state.setdefault("last_analyzed_at", {})
                now = _now_ts()
                for fp in changed:
                    if now - last.get(fp, 0) < WATCH_DEBOUNCE_SEC:
                        continue
                    last[fp] = now
                    asyncio.create_task(_watch_analyze_file(fp, root_path))
            except Exception:
                pass


async def _watch_analyze_file(file_path: str, root_path: str) -> None:
    """변경된 파일 자동 분석 + broadcast"""
    try:
        p = Path(file_path)
        content = p.read_text(encoding="utf-8", errors="ignore")
        if len(content) < 10 or len(content) > 30000:
            return
        viz = await _viz_agent_call(content, input_kind=f"watch_change ({p.name})")
        viz.setdefault("files_touched", [file_path])
        viz["summary"] = f"🔄 변경 감지 — " + (viz.get("summary") or p.name)
        record = {"ts": _now_iso(), "data": {
            "hook_event_name": "_summary", "session_id": f"_watch_{root_path}",
            "reason": "file_change", "event_count": 0,
            "llm_used": bool(await _get_key()),
            **viz}}
        async with _lock:
            _history.append(record)
        await _broadcast(record)
    except Exception:
        pass


@app.post("/watch/start")
async def watch_start(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    path = (data.get("path") or "").strip()
    if not path:
        return {"ok": False, "error": "path 비어있음"}
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        return {"ok": False, "error": "디렉토리 아님"}
    _watch_targets[str(p)] = {
        "mtimes": _scan_mtimes(p),  # 초기 스냅샷
        "last_analyzed_at": {},
        "paused": False,
    }
    return {"ok": True, "path": str(p), "file_count": len(_watch_targets[str(p)]["mtimes"])}


@app.post("/watch/stop")
async def watch_stop(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}
    path = (data.get("path") or "").strip()
    if path:
        p = str(Path(path).expanduser().resolve())
        _watch_targets.pop(p, None)
        return {"ok": True, "removed": p}
    _watch_targets.clear()
    return {"ok": True, "removed": "all"}


@app.get("/watch/status")
async def watch_status() -> dict[str, Any]:
    return {
        "ok": True,
        "watching": [
            {"path": p, "files": len(s.get("mtimes", {})), "paused": s.get("paused", False)}
            for p, s in _watch_targets.items()
        ],
    }


@app.on_event("startup")
async def _on_startup() -> None:
    asyncio.create_task(_periodic_summary_loop())
    asyncio.create_task(_watcher_loop())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
