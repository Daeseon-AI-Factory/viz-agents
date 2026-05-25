"""Repo Analyzer — repo URL/경로 → viz_kind+viz_data.

핵심 원칙 (CORE.md 따름):
  - 자체 깊은 분석 X — LLM 에 위임
  - 결과는 viz_kind 표준에 맞게
  - 미래에 별도 서비스로 분리 가능 (모듈 분리 구조)

지원:
  - 로컬 디렉토리 경로
  - GitHub URL (public 만, fetch tree)
  - 향후: GitLab, Bitbucket
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Awaitable

import httpx


# 무시할 디렉토리 (분석 노이즈)
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    "dist", "build", ".next", ".nuxt", "target", "vendor",
    ".cache", ".pytest_cache", ".mypy_cache", "coverage",
}

# 주요 메타 파일 (project 의 정체 파악)
META_FILES = [
    "README.md", "README", "package.json", "pyproject.toml",
    "Cargo.toml", "go.mod", "Gemfile", "pom.xml", "build.gradle",
    "docker-compose.yml", "Dockerfile",
]


def build_tree_summary(root: Path, max_depth: int = 3, max_items: int = 200) -> str:
    """디렉토리를 텍스트 트리로 요약 (LLM 입력용)"""
    lines: list[str] = []

    def walk(d: Path, depth: int = 0):
        if depth > max_depth or len(lines) >= max_items:
            return
        try:
            children = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for child in children[:30]:
                if len(lines) >= max_items:
                    break
                if child.name.startswith(".") and child.name not in (".gitignore", ".env.example"):
                    continue
                if child.name in SKIP_DIRS:
                    continue
                indent = "  " * depth
                if child.is_dir():
                    lines.append(f"{indent}📁 {child.name}/")
                    walk(child, depth + 1)
                else:
                    suffix = child.suffix.lower()
                    icon = "🐍" if suffix == ".py" else "📜" if suffix in (".js", ".ts", ".jsx", ".tsx") else "📄"
                    lines.append(f"{indent}{icon} {child.name}")
        except PermissionError:
            pass

    walk(root)
    return "\n".join(lines)


def read_meta_files(root: Path) -> list[dict]:
    """주요 메타 파일 내용 일부 (project 정체 파악용)"""
    out = []
    for fname in META_FILES:
        f = root / fname
        if f.exists() and f.is_file():
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")[:1500]
                out.append({"name": fname, "content": content})
            except Exception:
                pass
    return out


def count_files_by_ext(root: Path, max_walk: int = 5000) -> dict[str, int]:
    """확장자별 파일 카운트 (언어 추정)"""
    counts: dict[str, int] = {}
    walked = 0
    for p in root.rglob("*"):
        walked += 1
        if walked > max_walk:
            break
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            ext = p.suffix.lower() or "no_ext"
            counts[ext] = counts.get(ext, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1])[:20])


async def analyze_local_repo(
    path: str,
    llm_call: Callable[[str, str], Awaitable[dict]],
    deep: bool = True,
) -> dict[str, Any]:
    """로컬 디렉토리 → 2-step 분석.

    Step 1: 메타 + 트리 → 큰 그림 viz (arch)
    Step 2 (deep=True): LLM 이 핵심 파일 선택 → 각 파일 깊이 분석 → callgraph
    """
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        return {"error": f"디렉토리 아님: {path}"}

    tree = build_tree_summary(p)
    metas = read_meta_files(p)
    ext_counts = count_files_by_ext(p)

    meta_text = "\n\n".join(
        f"--- {m['name']} (첫 1500자) ---\n{m['content']}"
        for m in metas
    )
    ext_text = ", ".join(f"{ext}: {n}" for ext, n in ext_counts.items())
    input_text = (
        f"Repo 이름: {p.name}\n"
        f"경로: {p}\n\n"
        f"파일 확장자 분포:\n{ext_text}\n\n"
        f"디렉토리 트리:\n{tree}\n\n"
        f"주요 메타 파일:\n{meta_text}"
    )

    # Step 1: 큰 그림 viz
    viz = await llm_call(input_text, f"local_repo ({p.name})")
    viz.setdefault("files_touched", [str(p)])
    viz["_repo_meta"] = {
        "path": str(p), "name": p.name,
        "file_counts": ext_counts,
        "total_files_listed": sum(ext_counts.values()),
    }

    # Step 2: deep 모드 — 핵심 파일 선택 + 깊이 분석
    if deep:
        deep_results = await _deep_analyze(p, input_text, llm_call)
        viz["_deep"] = deep_results

    return viz


async def _select_key_files(
    repo_summary_input: str,
    llm_call: Callable[[str, str], Awaitable[dict]],
) -> list[str]:
    """LLM 이 repo 메타 보고 핵심 파일 3-5개 선택"""
    prompt = (
        repo_summary_input +
        "\n\n위 repo 에서 가장 핵심적인 코드 파일 3-5개를 골라주세요. "
        "(README/설정 파일 X, 실제 로직 파일만)\n\n"
        "출력은 다음 JSON 만:\n"
        '{"summary": "이 repo 의 핵심 한 줄", "viz_kind": "table", '
        '"viz_data": {"headers": ["path"], "rows": [["path1"], ["path2"], ...]}}'
    )
    result = await llm_call(prompt, "select_key_files")
    paths = []
    try:
        rows = (result.get("viz_data") or {}).get("rows", [])
        for row in rows[:5]:
            if row and isinstance(row, list):
                paths.append(str(row[0]))
    except Exception:
        pass
    return paths


async def _deep_analyze(
    root: Path,
    repo_summary_input: str,
    llm_call: Callable[[str, str], Awaitable[dict]],
) -> dict[str, Any]:
    """Step 2: 핵심 파일 식별 + 각자 깊이 분석"""
    key_paths = await _select_key_files(repo_summary_input, llm_call)
    if not key_paths:
        return {"key_files": [], "analyses": []}

    # 경로 해석: 상대경로면 root 기준
    resolved = []
    for path_str in key_paths:
        # README 의 코드 블록 노이즈 가능 — 안전하게 resolve
        candidate = (root / path_str).resolve() if not Path(path_str).is_absolute() else Path(path_str)
        # repo 안에 있는지 확인 (path traversal 방지)
        try:
            candidate.relative_to(root)
            if candidate.exists() and candidate.is_file():
                resolved.append(candidate)
        except ValueError:
            pass

    # 각 핵심 파일 깊이 분석 (병렬)
    async def _analyze_one(file_path: Path) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if len(content) > 8000:
                content = content[:8000] + "\n... (truncated)"
            input_text = f"파일: {file_path.name}\n경로: {file_path}\n\n코드:\n{content}"
            viz = await llm_call(input_text, f"deep_file ({file_path.name})")
            return {
                "file": str(file_path.relative_to(root)),
                "viz": viz,
            }
        except Exception as e:
            return {"file": str(file_path), "error": str(e)[:100]}

    analyses = await asyncio.gather(*[_analyze_one(f) for f in resolved[:5]])
    return {
        "key_files": [str(f.relative_to(root)) for f in resolved],
        "analyses": [a for a in analyses if a],
    }


async def analyze_github_repo(
    url: str,
    llm_call: Callable[[str, str], Awaitable[dict]],
) -> dict[str, Any]:
    """GitHub URL → tree fetch → LLM 위임"""
    import re
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$", url.strip())
    if not m:
        return {"error": "GitHub URL 형식 아님"}
    owner, repo = m.groups()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 기본 정보
            info_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if info_resp.status_code != 200:
                return {"error": f"GitHub API {info_resp.status_code}"}
            info = info_resp.json()

            # tree (default branch)
            branch = info.get("default_branch", "main")
            tree_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            tree_data = tree_resp.json() if tree_resp.status_code == 200 else {"tree": []}
    except Exception as e:
        return {"error": f"네트워크: {str(e)[:100]}"}

    # tree 요약 (path 만)
    files = [t["path"] for t in tree_data.get("tree", [])[:300]
             if not any(part in SKIP_DIRS for part in t["path"].split("/"))]
    tree_text = "\n".join(files[:200])

    # 확장자 카운트
    ext_counts: dict[str, int] = {}
    for f in files:
        ext = Path(f).suffix.lower() or "no_ext"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    ext_counts = dict(sorted(ext_counts.items(), key=lambda x: -x[1])[:15])
    ext_text = ", ".join(f"{ext}: {n}" for ext, n in ext_counts.items())

    input_text = (
        f"GitHub Repo: {owner}/{repo}\n"
        f"설명: {info.get('description', '') or ''}\n"
        f"언어: {info.get('language', '')}\n"
        f"별표: {info.get('stargazers_count', 0)}\n\n"
        f"확장자 분포: {ext_text}\n\n"
        f"파일 트리 (첫 200개):\n{tree_text}"
    )

    viz = await llm_call(input_text, f"github_repo ({owner}/{repo})")
    viz.setdefault("files_touched", [url])
    viz["_repo_meta"] = {
        "url": url, "owner": owner, "repo": repo,
        "description": info.get("description"),
        "language": info.get("language"),
        "stars": info.get("stargazers_count"),
        "file_count": len(files),
    }
    return viz


async def analyze_repo(
    target: str,
    llm_call: Callable[[str, str], Awaitable[dict]],
) -> dict[str, Any]:
    """auto detection: URL vs 로컬 경로"""
    target = target.strip()
    if target.startswith("http://") or target.startswith("https://"):
        return await analyze_github_repo(target, llm_call)
    else:
        return await analyze_local_repo(target, llm_call)
