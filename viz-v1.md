# VIZ Service — V1

**[← Index](./viz-README.md)** · **[← v0](./viz-v0.md)** · **[v2 →](./viz-v2.md)**

---

## V1 — Multi-file package import graph

### Upgrade from V0
V0 handles one file. V1 takes a package directory and produces (a) the per-file call graphs (V0's logic) PLUS (b) a higher-level import graph between files/modules. Two Mermaid outputs: zoomed-in (within a file) and zoomed-out (across files).

### Exit criteria
- Accepts a directory path
- Returns: per-file call graphs + cross-file import graph + a combined "module-level" Mermaid
- Detects circular imports and flags them
- Eval on 3 sample packages of 3-8 files each

### Prompt to paste into Claude Code

```
Build services/viz/v1/ — adds multi-file analysis to V0.

STEP 1: Read services/viz/v0/.

STEP 2: Build services/viz/v1/.

services/viz/v1/src/viz/agent.py:
  Reuse build_call_graph from V0 per file.
  Add:
  def build_import_graph(pkg_dir: str) -> dict:
    Walk pkg_dir for *.py files. Parse each, find ast.Import and ast.ImportFrom nodes.
    Build edges: file -> imported_module (only edges where target is within pkg_dir count; external imports are recorded separately).
    Detect cycles via DFS.
    Return {"file_nodes":[...],"import_edges":[...],"external_imports":[...],"cycles":[[file1,file2,...]],"mermaid_module":"graph LR\n..."}

  def analyze_package(pkg_dir: str) -> dict:
    file_graphs = {file: build_call_graph(file) for file in py_files}
    import_graph = build_import_graph(pkg_dir)
    Return both.

services/viz/v1/src/viz/api.py:
  "upgrade_from_previous":"V0 worked on a single file. V1 accepts a package directory, computes per-file call graphs plus a cross-file import graph, detects circular imports, and emits both zoomed-in (per-file) and zoomed-out (module) Mermaid views.",
  "new_capabilities":["package-level analysis","cross-file import graph","circular import detection","two-level Mermaid output"]
  run(input) — input requires pkg_dir.

shared/eval-datasets/viz-v1.jsonl — 3 packages (CC creates fixture dirs):
  - small_clean (4 files, no cycles)
  - circular (3 files with a deliberate import cycle)
  - flat (5 files, all import from a shared utils.py)
  Each item: expected_files, expected_cycles, expected_import_edges.

services/viz/v1/eval.py:
  For each: did V1 find the right number of files, the cycles, the import edges?
  Aggregate. Save to results/viz/v1/run-{timestamp}.json.
```

### After CC completes
1. Cycles caught correctly? (binary check)
2. Render the circular package's module mermaid — is the cycle visible?
3. Is the zoomed-out view actually useful, or is it just a bunch of file boxes?

---

**Next:** [viz-v2.md](./viz-v2.md)
