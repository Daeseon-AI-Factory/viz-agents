"""viz-core — AI 출력 시각화 R&D 레이어. 단순화 빌드.

핵심:
  - 입력: Hook 이벤트 / 자연어 요청 / 외부 POST (3가지만)
  - 출력: 24종 viz_kind 자동 매핑 (Phase 1~5 포함)
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
import io
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

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
  "viz_kind": "diff|table|gauge|flow|badge|code|animation|kpi|journey|arch|whatif|mermaid|timeseries|bar|funnel|heatmap|kanban|waterfall|cohort|crud|userflow|screenmap|depgraph|concept|none",
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
  - mermaid   : ★ 무한 시각 (mermaid.js 문법). {"code":"mermaid 문법", "title":"한 줄 설명"}
                예시: sequenceDiagram / classDiagram / erDiagram / stateDiagram /
                     gantt / flowchart / mindmap / timeline / gitGraph
                code 안에 mermaid 문법 그대로 쓰기 (들여쓰기 정확히).
  - timeseries: ★ 시계열 line chart (시간축 추세). {"title":"...", "labels":["Jan","Feb",...], "series":[{"label":"매출","values":[100,120,...],"color":"#58a6ff"}]}
                매출/사용자/응답시간 등 시간 흐름 데이터에 우선.
  - bar       : ★ 카테고리 비교 막대 차트. {"title":"...", "labels":["A","B","C"], "values":[10,20,15], "horizontal":false}
                또는 multi-series: {"series":[{"label":"...","values":[...]},...]}
  - funnel    : ★ 전환 깔때기. {"title":"...", "stages":[{"name":"방문","value":10000},{"name":"가입","value":1000},...]}
                사용자 전환 분석에 필수. 자동으로 conversion% 와 drop% 계산됨.
  - heatmap   : ★ 시간×지표 분포 매트릭스. {"title":"...", "labels_x":["월","화",...], "labels_y":["server-a","server-b",...], "matrix":[[10,20,...],[...]]}
                CPU/메모리/트래픽 시간대별 분포, 요일×시간 활동량 등.
  - kanban    : ★ 작업 보드. {"title":"...", "columns":[{"name":"TODO","cards":[{"title":"...","assignee":"...","tags":["..."]}]},{"name":"DOING",...},{"name":"DONE",...}]}
                할 일 / 진행 중 / 완료 - 프로젝트 진척 상황.
  - waterfall : ★ 분산 추적 스팬. {"title":"...", "spans":[{"name":"API /users","service":"gateway","start_ms":0,"duration_ms":120,"color":"#58a6ff"},{"name":"DB query","service":"postgres","start_ms":30,"duration_ms":50},...]}
                API 요청 경로 + 각 서비스 호출 시간 - 성능 분석.
  - cohort    : ★ retention 매트릭스. {"title":"...", "cohorts":[{"label":"2026-01","initial":1000,"retention":[1000,650,420,300,...]},{"label":"2026-02","initial":1200,"retention":[1200,800,...]}]}
                월별 가입자 유지율 - 비즈니스 핵심 지표.
  - crud      : ★ CRUD 권한 매트릭스. {"title":"...", "entities":["User","Order","Payment"], "actors":["User","Admin","Guest"], "matrix":[[["C","R","U","D"],["C","R","U","D"],["R"]], ...]}
                엔티티 × 역할 권한 (PM/설계 핵심). matrix[i][j] = entities[i]에 대한 actors[j]의 권한 액션 배열.
  - userflow  : ★ 사용자 동선 + 분기. {"title":"...", "nodes":[{"id":"visit","label":"방문","kind":"start|screen|decision|action|end"}], "edges":[{"from":"visit","to":"login","label":"클릭"}]}
                결정 노드(decision)는 마름모, 화면(screen)은 사각형. 시작/끝/액션 구분.
  - screenmap : ★ 화면 박스 + 전환. {"title":"...", "screens":[{"id":"home","title":"홈","x":0,"y":0,"items":["로고","검색바","상품 리스트"]}], "transitions":[{"from":"home","to":"detail","action":"상품 클릭"}]}
                x/y는 grid 좌표 (정수, 0부터). UX/PM 단계 와이어프레임.
  - depgraph  : ★ 서비스 의존성 그래프. {"title":"...", "services":[{"id":"gw","label":"Gateway","kind":"frontend|api|service|db|cache|cdn|queue|external"}], "deps":[{"from":"gw","to":"auth","kind":"http|db|cache|queue"}]}
                마이크로서비스 의존도, 위→아래 데이터 흐름.
  - concept   : ★★ 기술 개념을 비유+시각+장단+실무로 설명 (병신도 이해). {"concept":"캐싱","tagline":"자주 쓰는 정보는 가까이","analogy":{"name":"책상 위 메모지","icon":"📝"},"comparison":{"without":{"icon":"🗄️","label":"DB까지 매번 감","steps":["요청","DB 찾기","디스크 읽기","응답"],"metric":"100ms"},"with":{"icon":"📝","label":"메모 먼저 봄","steps":["메모 확인"],"metric":"1ms"}},"tradeoffs":{"pros":["100배 빠름","DB 부담 ↓"],"cons":["메모리 ↑","오래된 정보 가능"]},"real_world":"API 응답, 세션"}
                buzzword 말고 실무언어. AI 가 추천하는 기술 (캐싱/Index/JWT/CDN/큐 등) 의 본질을 직관적으로.
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
                # ★ prompt caching: system prompt 캐싱 → 2-3배 빠름 + 90% 비용 ↓
                json={"model": MODEL, "max_tokens": 600,
                      "system": [{"type": "text", "text": SUMMARY_SYSTEM,
                                  "cache_control": {"type": "ephemeral"}}],
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


@app.get("/showcase")
async def showcase() -> FileResponse:
    return FileResponse(HERE / "showcase.html")


@app.get("/spec")
async def spec_page() -> FileResponse:
    return FileResponse(HERE / "spec.html")


@app.get("/AI_GUIDE.md")
async def ai_guide() -> FileResponse:
    return FileResponse(HERE / "AI_GUIDE.md", media_type="text/markdown")


@app.get("/i18n.js")
async def i18n_js() -> FileResponse:
    return FileResponse(HERE / "i18n.js", media_type="application/javascript")


@app.get("/concepts.html")
async def concepts_page() -> FileResponse:
    return FileResponse(HERE / "concepts.html")


# ── ★ 개념 라이브러리 (본인 학습 자산) ──
# concepts/*.json 파일 = 1개 개념. 디스크 영구 저장.

CONCEPTS_DIR = HERE / "concepts"
CONCEPTS_DIR.mkdir(exist_ok=True)
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _list_concept_files() -> list[Path]:
    if not CONCEPTS_DIR.exists():
        return []
    return sorted(CONCEPTS_DIR.glob("*.json"))


def _read_concept(slug: str) -> dict | None:
    if not SLUG_PATTERN.match(slug or ""):
        return None
    p = CONCEPTS_DIR / f"{slug}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


@app.get("/concepts")
async def concepts_list() -> dict[str, Any]:
    """모든 개념 목록 (목록용 — 본문 데이터 작게)."""
    items = []
    for p in _list_concept_files():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            items.append({
                "slug": d.get("slug") or p.stem,
                "concept": d.get("concept") or p.stem,
                "tagline": d.get("tagline") or "",
                "category": d.get("category") or "",
                "tags": d.get("tags") or [],
                "analogy": d.get("analogy") or {},
            })
        except Exception:
            continue
    return {"ok": True, "count": len(items), "items": items}


@app.get("/concepts/{slug}")
async def concepts_get(slug: str) -> dict[str, Any]:
    d = _read_concept(slug)
    if not d:
        return {"ok": False, "error": "찾을 수 없음"}
    return {"ok": True, "concept": d}


@app.post("/concepts")
async def concepts_add(request: Request) -> dict[str, Any]:
    """새 개념 추가 / 수정. body = concept JSON 전체."""
    raw = await request.body()
    try:
        d = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    if not isinstance(d, dict):
        return {"ok": False, "error": "object 형식 필요"}
    slug = (d.get("slug") or "").strip().lower()
    if not SLUG_PATTERN.match(slug):
        return {"ok": False, "error": "slug 필요 (소문자/숫자/하이픈, 최대 64자, a-z0-9 로 시작)"}
    if not d.get("concept"):
        return {"ok": False, "error": "concept 필드 필수"}
    p = CONCEPTS_DIR / f"{slug}.json"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "slug": slug, "saved_to": str(p.name)}


@app.delete("/concepts/{slug}")
async def concepts_delete(slug: str) -> dict[str, Any]:
    if not SLUG_PATTERN.match(slug or ""):
        return {"ok": False, "error": "slug 형식 오류"}
    p = CONCEPTS_DIR / f"{slug}.json"
    if not p.exists():
        return {"ok": False, "error": "존재하지 않음"}
    p.unlink()
    return {"ok": True, "deleted": slug}


# ── ★ 통합 자산 라이브러리 (모든 viz_kind) ──
# library/{viz_kind}/{slug}.json — 디스크 영구.
# concept 만이 아니라 모든 24종 viz_kind 등록 가능.

LIBRARY_DIR = HERE / "library"
LIBRARY_DIR.mkdir(exist_ok=True)


def _library_path(viz_kind: str, slug: str) -> Path | None:
    if not slug or not SLUG_PATTERN.match(slug):
        return None
    if not viz_kind or viz_kind not in VALID_VIZ_KINDS:
        return None
    sub = LIBRARY_DIR / viz_kind
    sub.mkdir(exist_ok=True)
    return sub / f"{slug}.json"


def _import_concepts_to_library() -> int:
    """기존 concepts/*.json 을 library/concept/ 로 자동 복사 (덮어쓰기 X)."""
    if not CONCEPTS_DIR.exists():
        return 0
    target_dir = LIBRARY_DIR / "concept"
    target_dir.mkdir(exist_ok=True)
    imported = 0
    for src in CONCEPTS_DIR.glob("*.json"):
        dst = target_dir / src.name
        if dst.exists():
            continue
        try:
            d = json.loads(src.read_text(encoding="utf-8"))
            if "viz_kind" not in d:
                d["viz_kind"] = "concept"
            dst.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            imported += 1
        except Exception:
            continue
    return imported


_imported_count = _import_concepts_to_library()


# ── ★ 사용 통계 (영구 로그) — 포폴 어필용 ──
USAGE_LOG = HERE / "usage_log.jsonl"


def _log_usage(kind: str, viz_kind: str | None = None, slug: str | None = None, source: str | None = None) -> None:
    """모든 viz 표시 / 자산 push 기록. jsonl append 만 — 빠름, 휘발 X."""
    try:
        entry = {
            "ts": _now_iso(),
            "date": _now_iso()[:10],
            "kind": kind,
            "viz_kind": viz_kind,
            "slug": slug,
            "source": source,
        }
        with USAGE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


@app.get("/stats")
async def stats_page() -> FileResponse:
    return FileResponse(HERE / "stats.html")


@app.get("/stats/data")
async def stats_data() -> dict[str, Any]:
    """사용 통계 집계 — 캘린더, top 자산, 메트릭."""
    entries: list[dict] = []
    if USAGE_LOG.exists():
        try:
            for line in USAGE_LOG.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        except Exception:
            pass

    # 캘린더 (date → count)
    calendar: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    by_asset: dict[str, int] = {}  # "viz_kind/slug" → count
    by_source: dict[str, int] = {}
    for e in entries:
        d = e.get("date") or (e.get("ts") or "")[:10]
        if d:
            calendar[d] = calendar.get(d, 0) + 1
        vk = e.get("viz_kind")
        if vk:
            by_kind[vk] = by_kind.get(vk, 0) + 1
        slug = e.get("slug")
        if vk and slug:
            key = f"{vk}/{slug}"
            by_asset[key] = by_asset.get(key, 0) + 1
        src = e.get("source") or e.get("kind")
        if src:
            by_source[src] = by_source.get(src, 0) + 1

    # 자산 라이브러리 통계 (자산 추가 시점은 mtime)
    asset_count = 0
    asset_kinds: dict[str, int] = {}
    if LIBRARY_DIR.exists():
        for sub in LIBRARY_DIR.iterdir():
            if not sub.is_dir():
                continue
            files = list(sub.glob("*.json"))
            if files:
                asset_count += len(files)
                asset_kinds[sub.name] = len(files)

    # top assets
    top_assets = sorted(by_asset.items(), key=lambda x: x[1], reverse=True)[:10]

    # 최근 사용
    last_used = entries[-1].get("ts") if entries else None

    return {
        "ok": True,
        "total_events": len(entries),
        "first_event": entries[0].get("ts") if entries else None,
        "last_event": last_used,
        "calendar": calendar,
        "by_viz_kind": by_kind,
        "by_source": by_source,
        "top_assets": [{"key": k, "count": c} for k, c in top_assets],
        "asset_count": asset_count,
        "asset_kinds": asset_kinds,
    }


@app.get("/library")
async def library_list(viz_kind: str | None = None, lang: str | None = None) -> dict[str, Any]:
    """모든 자산 목록. ?viz_kind=concept 필터 + ?lang=en|ko 다국어."""
    items = []
    kinds_to_scan = [viz_kind] if viz_kind else None
    if kinds_to_scan is None:
        kinds_to_scan = [d.name for d in LIBRARY_DIR.iterdir() if d.is_dir()]
    lang = (lang or "").lower() if lang else None
    for kind in kinds_to_scan:
        sub = LIBRARY_DIR / kind
        if not sub.exists() or not sub.is_dir():
            continue
        for p in sorted(sub.glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                # i18n 적용 (lang 지정된 경우)
                if lang and isinstance(d.get("i18n"), dict):
                    loc = d["i18n"].get(lang)
                    if isinstance(loc, dict):
                        d = {**d, **loc}
                items.append({
                    "slug": d.get("slug") or p.stem,
                    "viz_kind": d.get("viz_kind") or kind,
                    "title": d.get("title") or d.get("concept") or p.stem,
                    "tagline": d.get("tagline") or "",
                    "category": d.get("category") or "",
                    "tags": d.get("tags") or [],
                    "icon": (d.get("analogy") or {}).get("icon") or "",
                    "analogy_name": (d.get("analogy") or {}).get("name") or "",
                })
            except Exception:
                continue
    return {"ok": True, "count": len(items), "items": items}


@app.get("/library/{viz_kind}/{slug}")
async def library_get(viz_kind: str, slug: str) -> dict[str, Any]:
    p = _library_path(viz_kind, slug)
    if not p or not p.exists():
        return {"ok": False, "error": "찾을 수 없음"}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {"ok": True, "asset": d}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


@app.post("/library")
async def library_add(request: Request) -> dict[str, Any]:
    """새 자산 추가 / 수정. body: {slug, viz_kind, title?, ...kind별 schema...}"""
    raw = await request.body()
    try:
        d = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    if not isinstance(d, dict):
        return {"ok": False, "error": "object 형식 필요"}
    slug = (d.get("slug") or "").strip().lower()
    viz_kind = (d.get("viz_kind") or "").strip().lower()
    if not SLUG_PATTERN.match(slug):
        return {"ok": False, "error": "slug 필요 (소문자/숫자/하이픈)"}
    if viz_kind not in VALID_VIZ_KINDS:
        return {"ok": False, "error": f"viz_kind 유효하지 않음. 가능: {sorted(VALID_VIZ_KINDS)}"}
    p = _library_path(viz_kind, slug)
    if not p:
        return {"ok": False, "error": "경로 생성 실패"}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "slug": slug, "viz_kind": viz_kind, "saved_to": f"library/{viz_kind}/{slug}.json"}


@app.delete("/library/{viz_kind}/{slug}")
async def library_delete(viz_kind: str, slug: str) -> dict[str, Any]:
    p = _library_path(viz_kind, slug)
    if not p or not p.exists():
        return {"ok": False, "error": "존재하지 않음"}
    p.unlink()
    return {"ok": True, "deleted": f"{viz_kind}/{slug}"}


@app.post("/library/{viz_kind}/{slug}/show")
async def library_show(viz_kind: str, slug: str) -> dict[str, Any]:
    """자산을 viz 로 옆 탭에 푸시 (브로드캐스트)."""
    p = _library_path(viz_kind, slug)
    if not p or not p.exists():
        return {"ok": False, "error": "찾을 수 없음"}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    # concept 는 viz_data 가 자기 자신, 그 외는 viz_data 필드 우선
    viz_data = d.get("viz_data") or d
    record = {
        "ts": _now_iso(),
        "data": {
            "hook_event_name": "_summary",
            "session_id": "_library",
            "reason": "library_show",
            "event_count": 0,
            "llm_used": False,
            "summary": f"자산: {d.get('title') or d.get('concept') or slug}",
            "next_step": "",
            "viz_kind": viz_kind,
            "viz_reason": "자산 라이브러리에서 직접 표시",
            "viz_data": viz_data,
        }
    }
    async with _lock:
        _history.append(record)
    await _broadcast(record)
    _log_usage(kind="library_show", viz_kind=viz_kind, slug=slug)
    return {"ok": True, "slug": slug, "viz_kind": viz_kind, "pushed": True}


@app.get("/library.html")
async def library_page() -> FileResponse:
    return FileResponse(HERE / "library.html")


@app.get("/library/stats")
async def library_stats() -> dict[str, Any]:
    """라이브러리 통계 — 첫 화면용."""
    counts: dict[str, int] = {}
    total_files = 0
    total_bytes = 0
    if LIBRARY_DIR.exists():
        for sub in LIBRARY_DIR.iterdir():
            if not sub.is_dir():
                continue
            files = list(sub.glob("*.json"))
            if files:
                counts[sub.name] = len(files)
                total_files += len(files)
                for f in files:
                    total_bytes += f.stat().st_size
    return {"ok": True, "total": total_files,
            "kinds_used": len(counts), "by_kind": counts,
            "total_bytes": total_bytes}


@app.get("/library/export")
async def library_export() -> Response:
    """전체 library 를 zip 으로 다운로드 (백업/이전)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if LIBRARY_DIR.exists():
            for sub in LIBRARY_DIR.iterdir():
                if not sub.is_dir():
                    continue
                for f in sub.glob("*.json"):
                    rel = f"library/{sub.name}/{f.name}"
                    zf.write(f, rel)
    buf.seek(0)
    fname = f"viz-core-library-{_now_iso().replace(':','-')}.zip"
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.post("/library/import")
async def library_import(request: Request) -> dict[str, Any]:
    """zip 또는 JSON 배열 업로드 → library 에 박기.

    Content-Type: application/zip → zip 안 library/{kind}/{slug}.json 들을 읽어서 박음
    Content-Type: application/json → {"items":[{viz_kind, slug, ...}]} 배열
    """
    raw = await request.body()
    ct = request.headers.get("content-type", "").lower()
    imported = 0
    skipped = 0
    errors: list[str] = []

    if "zip" in ct or raw[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for name in zf.namelist():
                    if not name.endswith(".json"):
                        continue
                    parts = name.replace("\\", "/").split("/")
                    # library/{kind}/{slug}.json 또는 {kind}/{slug}.json
                    if len(parts) >= 2:
                        kind = parts[-2]
                        fname = parts[-1]
                    else:
                        skipped += 1
                        continue
                    if kind not in VALID_VIZ_KINDS:
                        skipped += 1; continue
                    slug = fname[:-5].lower()
                    if not SLUG_PATTERN.match(slug):
                        skipped += 1; continue
                    try:
                        d = json.loads(zf.read(name).decode("utf-8"))
                    except Exception as e:
                        errors.append(f"{name}: {e}"); skipped += 1; continue
                    p = _library_path(kind, slug)
                    if p:
                        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                        imported += 1
        except zipfile.BadZipFile:
            return {"ok": False, "error": "잘못된 zip 파일"}
    else:
        try:
            payload = json.loads(raw) if raw else {}
        except Exception as e:
            return {"ok": False, "error": f"JSON 파싱: {e}"}
        items = payload.get("items") if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
        for item in items or []:
            if not isinstance(item, dict):
                skipped += 1; continue
            kind = (item.get("viz_kind") or "").strip().lower()
            slug = (item.get("slug") or "").strip().lower()
            if kind not in VALID_VIZ_KINDS or not SLUG_PATTERN.match(slug):
                skipped += 1; continue
            p = _library_path(kind, slug)
            if p:
                p.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
                imported += 1

    return {"ok": True, "imported": imported, "skipped": skipped, "errors": errors[:5]}


@app.post("/concepts/{slug}/show")
async def concepts_show(slug: str) -> dict[str, Any]:
    """해당 개념을 viz 로 옆 탭에 푸시 (브로드캐스트)."""
    d = _read_concept(slug)
    if not d:
        return {"ok": False, "error": "찾을 수 없음"}
    record = {
        "ts": _now_iso(),
        "data": {
            "hook_event_name": "_summary",
            "session_id": "_concept",
            "reason": "concept_show",
            "event_count": 0,
            "llm_used": False,
            "summary": f"개념: {d.get('concept', slug)}",
            "next_step": "",
            "viz_kind": "concept",
            "viz_reason": "개념 라이브러리에서 직접 표시",
            "viz_data": d,
        }
    }
    async with _lock:
        _history.append(record)
    await _broadcast(record)
    return {"ok": True, "slug": slug, "pushed": True}


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
                json={"model": MODEL, "max_tokens": 2000,
                      "system": [{"type": "text", "text": SUMMARY_SYSTEM,
                                  "cache_control": {"type": "ephemeral"}}],
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
        _log_usage(kind="viz_request", viz_kind=parsed.get("viz_kind"), source="user_nl")
        return {"ok": True, "viz": parsed}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ── ★ viz-spec 마커 파서 (다른 AI 출력에서 직접 추출, LLM 호출 X) ──
# AI 가 응답에 ```viz-spec ... ``` 박으면 자동 추출 → 즉시 렌더.
# 핵심: 메인 응답은 그대로 보이고, 마커만 뽑아 사이드카로 사용.

VIZ_SPEC_PATTERN = re.compile(r"```viz-spec\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)

VALID_VIZ_KINDS = {
    "diff", "table", "gauge", "flow", "badge", "code", "animation",
    "kpi", "journey", "arch", "whatif", "mermaid", "callgraph",
    "timeseries", "bar", "funnel", "heatmap", "kanban", "waterfall", "cohort",
    "crud", "userflow", "screenmap", "depgraph",
    "concept",
}


def _extract_viz_specs(text: str) -> list[dict]:
    """AI 출력 텍스트에서 viz-spec 코드펜스 모두 추출.

    형식 1: ```viz-spec\\n{"viz_kind":"...", "data":{...}}\\n```
    형식 2: ```viz-spec\\n{"viz_kind":"...", "viz_data":{...}}\\n```
    옵션: "save": true / "slug": "..." 박혀있으면 library 에 자동 저장.
    """
    if not text:
        return []
    specs = []
    for match in VIZ_SPEC_PATTERN.finditer(text):
        body = (match.group(1) or "").strip()
        if not body:
            continue
        try:
            d = json.loads(body)
        except json.JSONDecodeError:
            continue
        if not isinstance(d, dict):
            continue
        kind = d.get("viz_kind")
        if not kind or kind not in VALID_VIZ_KINDS:
            continue
        viz_data = d.get("data") or d.get("viz_data") or {}
        specs.append({
            "viz_kind": kind,
            "viz_data": viz_data,
            "summary": d.get("summary") or d.get("title") or "",
            "viz_reason": d.get("reason") or "AI 가 viz-spec 마커로 직접 표시",
            "save": bool(d.get("save")),
            "slug": (d.get("slug") or "").strip().lower(),
            "title": d.get("title") or "",
            "tagline": d.get("tagline") or "",
            "category": d.get("category") or "",
            "tags": d.get("tags") or [],
        })
    return specs


@app.post("/viz/spec")
async def viz_spec(request: Request) -> dict[str, Any]:
    """AI 출력 텍스트 받아 viz-spec 마커 자동 추출 + 브로드캐스트.

    Body: {"text": "AI 응답 전문", "source": "선택 — claude/gpt/cursor/...", "session_id": "선택"}
    Returns: {"ok": True, "count": N, "specs": [{viz_kind, ...}], "raw": text}
    """
    raw = await request.body()
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return {"ok": False, "error": "JSON 파싱"}
    text = (data.get("text") or "").strip()
    if not text:
        return {"ok": False, "error": "text 필드 비어있음"}
    source = (data.get("source") or "external_ai").strip()
    session_id = (data.get("session_id") or "_viz_spec").strip()

    specs = _extract_viz_specs(text)
    if not specs:
        return {"ok": True, "count": 0, "specs": [],
                "note": "viz-spec 마커 없음. AI 응답에 ```viz-spec ... ``` 박혀있어야 추출됨."}

    sent = []
    saved = []
    for spec in specs:
        record = {
            "ts": _now_iso(),
            "data": {
                "hook_event_name": "_summary",
                "session_id": session_id,
                "reason": "viz_spec_marker",
                "event_count": 0,
                "llm_used": False,
                "source": source,
                "summary": spec.get("summary") or f"{spec['viz_kind']} viz",
                "next_step": "",
                "viz_kind": spec["viz_kind"],
                "viz_reason": spec["viz_reason"],
                "viz_data": spec["viz_data"],
            }
        }
        async with _lock:
            _history.append(record)
        await _broadcast(record)
        _log_usage(kind="viz_spec", viz_kind=spec["viz_kind"], source=source)
        sent.append({"viz_kind": spec["viz_kind"]})

        # ★ AI 가 save:true 박았으면 library 에 자동 저장
        if spec["save"] and spec["slug"] and SLUG_PATTERN.match(spec["slug"]):
            p = _library_path(spec["viz_kind"], spec["slug"])
            if p:
                merged = {
                    "slug": spec["slug"],
                    "viz_kind": spec["viz_kind"],
                    "title": spec["title"] or spec.get("summary") or spec["slug"],
                    "tagline": spec["tagline"],
                    "category": spec["category"],
                    "tags": spec["tags"],
                    **(spec["viz_data"] if isinstance(spec["viz_data"], dict) else {}),
                }
                p.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
                _log_usage(kind="auto_save", viz_kind=spec["viz_kind"], slug=spec["slug"], source=source)
                saved.append(f"{spec['viz_kind']}/{spec['slug']}")

    return {"ok": True, "count": len(sent), "specs": sent, "auto_saved": saved, "llm_used": False}


# ── ★ 시각화 specialist 에이전트 (LLM 위임) ──
# 핵심: 자체 분석 X. Claude 에게 "이 입력을 viz_kind+viz_data 로" 위임.
# 자세히는 CORE.md 참고.

VIZ_AGENT_SYSTEM = """당신은 viz-core 의 시각화 specialist AI 에이전트입니다.

역할: 입력 (코드/문서/repo/자연어) 을 받아서, 사용자가 0.5초에 이해할 시각으로 변환.

출력 (반드시 JSON, 다른 텍스트 X):
{
  "summary": "20-60자 한국어",
  "next_step": "0-30자 다음 할 일",
  "viz_kind": "callgraph|diff|table|gauge|flow|badge|code|animation|kpi|journey|arch|whatif|mermaid|timeseries|bar|funnel|heatmap|kanban|waterfall|cohort|crud|userflow|screenmap|depgraph|concept|none",
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
  - ★ 시계열 추세 → "timeseries" {title, labels:[...], series:[{label, values:[...], color}]}
       매출/사용자/응답시간 등 시간축 데이터에 우선.
  - ★ 카테고리 비교 → "bar" {title, labels:[...], values:[...] or series:[...], horizontal}
       지역별/제품별/팀별 비교에 우선.
  - ★ 전환 깔때기 → "funnel" {title, stages:[{name,value},...]}
       사용자 가입→결제→사용 같은 단계별 conversion 분석.
  - ★ 시간×지표 분포 → "heatmap" {title, labels_x:[...], labels_y:[...], matrix:[[..],[..]]}
       CPU/메모리/트래픽 요일×시간 히트맵, 활동량 분포.
  - ★ 작업 보드 → "kanban" {title, columns:[{name, cards:[{title, assignee, tags:[...]}]}]}
       TODO/DOING/DONE 진척 — 프로젝트 상황.
  - ★ 분산 추적 → "waterfall" {title, spans:[{name, service, start_ms, duration_ms, color}]}
       API 요청 경로 + 각 서비스 호출 시간 — 성능/병목 분석.
  - ★ Retention → "cohort" {title, cohorts:[{label, initial, retention:[...]}]}
       월별 가입자 유지율 — 비즈니스 핵심 지표.
  - ★ CRUD 권한 매트릭스 → "crud" {title, entities:[...], actors:[...], matrix:[[[C/R/U/D 부분집합],...],...]}
       엔티티×역할 권한, RACI, 접근 제어. matrix[i][j]는 entities[i]에 대한 actors[j] 가능 액션.
  - ★ 사용자 동선 + 분기 → "userflow" {title, nodes:[{id,label,kind:start|screen|decision|action|end}], edges:[{from,to,label}]}
       journey 와 차이: decision 노드 + 분기. 회원가입/결제 같은 흐름.
  - ★ 화면 + 전환 → "screenmap" {title, screens:[{id,title,x,y,items:[...]}], transitions:[{from,to,action}]}
       UX 와이어프레임, 화면 구성요소 + 화면간 이동.
  - ★ 서비스 의존도 → "depgraph" {title, services:[{id,label,kind:frontend|api|service|db|cache|cdn|queue|external}], deps:[{from,to,kind:http|db|cache|queue}]}
       마이크로서비스 구조, arch 보다 정밀 (방향 + 종류).
  - ★★ 기술 개념 이해 → "concept" {concept, tagline, analogy:{name,icon}, comparison:{without:{icon,label,steps:[...],metric}, with:{icon,label,steps:[...],metric}}, tradeoffs:{pros:[...],cons:[...]}, real_world}
       AI 가 캐싱/Index/JWT/CDN/큐 같은 거 추천할 때 — buzzword 말고 비유+시각+장단점으로 비-엔지니어도 즉시 이해. 책상 위 메모지/백과사전 색인/영화관 티켓 등 일상 비유 적극 활용.
  - ★ 무한 시각 → "mermaid" {code: "mermaid 문법", title: "한 줄 설명"}
       위 12종으로 표현 못하는 복잡한 시각이면 mermaid 사용:
       - sequenceDiagram (시퀀스 다이어그램, API 호출 순서)
       - classDiagram (UML 클래스, 상속/연관)
       - erDiagram (DB 테이블 관계)
       - stateDiagram-v2 (상태 머신)
       - gantt (간트 차트, 일정)
       - flowchart TD/LR (복잡한 분기, 의사결정)
       - mindmap (마인드맵)
       - timeline
       - gitGraph
       code 안에 정확한 mermaid 문법 (들여쓰기 정확히)

규칙:
- 분석은 깊이 X. 시각화 specialist 로서 어떻게 보여줄지에만 집중.
- 코드면 callgraph, 시스템 설명이면 arch, 흐름이면 animation 우선.
- 사용자 여정/시퀀스/상태/DB관계 등 복잡한 도식은 mermaid 적극.
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
                # ★ prompt caching + max_tokens 줄임
                json={"model": MODEL, "max_tokens": 1200,
                      "system": [{"type": "text", "text": VIZ_AGENT_SYSTEM,
                                  "cache_control": {"type": "ephemeral"}}],
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
