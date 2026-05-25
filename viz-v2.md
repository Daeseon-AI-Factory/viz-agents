# VIZ Service — V2

**[← Index](./viz-README.md)** · **[← v1](./viz-v1.md)** · **[v3 →](./viz-v3.md)**

---

## V2 — External dependency analysis

### Upgrade from V1
V1 maps internal imports. V2 looks outward: reads `pyproject.toml` / `requirements.txt`, identifies every external dependency, queries (offline-cached) metadata about each, and produces a dependency report: name, declared version, install-resolved version, license, last-update-age, known-CVE-flag (read from a local JSON if present, else "not checked").

LLM use here is optional and minimal — V2's job is mostly inventory. LLM enters for the "why does this codebase use library X" summary if requested.

### Exit criteria
- Reads pyproject.toml or requirements.txt
- For each dep: declared version, where in code it is imported, count of import sites
- Optional: enrichment from local `dep_metadata.json` cache file (license, CVE flags)
- Mermaid diagram: package + its external deps clustered by purpose category (LLM-classified into web/db/data/test/build/other)

### Prompt to paste into Claude Code

```
Build services/viz/v2/ — adds external dependency analysis.

STEP 1: Read services/viz/v1/.

STEP 2: Build services/viz/v2/.

services/viz/v2/src/viz/deps.py:
  def parse_deps(pkg_dir) -> list[dict]:
    Check for pyproject.toml first (read [project.dependencies] or [tool.poetry.dependencies]), else requirements.txt.
    Return [{"name":str,"declared_version":str,"source":"pyproject|requirements"}].

  def find_import_sites(pkg_dir, dep_name) -> list[dict]:
    Walk *.py, find ast.Import/ImportFrom matching dep_name (or top-level package of it). Return [{"file":path,"lineno":int}].

  def enrich_from_cache(deps, cache_path="dep_metadata.json") -> list[dict]:
    If cache file exists, merge fields: license, last_updated, cve_flags. If not, leave as None.

  def categorize_deps_llm(deps) -> dict[str,str]:
    Batch deps in groups of 20. System: "Classify each Python package by purpose: web|db|data|ml|test|build|cli|other. Output JSON {name:category}. ONLY JSON."
    Return merged dict.

services/viz/v2/src/viz/agent.py:
  In api.run:
    package_analysis = V1's analyze_package(pkg_dir)
    deps = parse_deps(pkg_dir)
    for d in deps: d["import_sites"] = find_import_sites(pkg_dir, d["name"])
    deps = enrich_from_cache(deps)
    categories = categorize_deps_llm(deps)
    deps_mermaid = build_deps_mermaid(deps, categories)  # subgraph per category
    Return {**package_analysis, "deps":deps,"deps_mermaid":deps_mermaid}

services/viz/v2/src/viz/api.py:
  "upgrade_from_previous":"V1 mapped internal imports only. V2 reads pyproject.toml/requirements.txt, lists every external dependency with declared version and import-site count, optionally enriches from a local metadata cache (license/CVE), and uses a single batched LLM call to categorize deps by purpose for the diagram.",
  "new_capabilities":["dependency manifest parsing","import-site tracing per dep","optional cache enrichment","LLM dep categorization","clustered dependency Mermaid"]

shared/eval-datasets/viz-v2.jsonl — 3 fixture packages with pyproject.toml. Expected: dep_count, presence of specific deps.

services/viz/v2/eval.py:
  Did V2 find the right number of deps? Categorization sensible (LLM-as-judge or hand-spot-check)?
```

### After CC completes
1. Are import_sites counts accurate?
2. Categorization quality — any deps put in "other" that should have been "db" or "web"?
3. If you provide a dep_metadata.json with CVE flags, does the diagram highlight flagged deps differently?

---

**Next:** [viz-v3.md](./viz-v3.md)
