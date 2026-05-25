# VIZ Service — V0

**[← Index](./viz-README.md)** · **[v1 →](./viz-v1.md)**

---

## V0 — Single-file call graph

### Upgrade from previous
*(baseline)*

### Goal
Given a single Python file, produce a Mermaid call graph (which functions call which).
Pure AST analysis — no LLM needed for V0. This establishes a "no-LLM baseline" so later LLM versions have something to compare cost/accuracy against.

### Exit criteria
- `services/viz/v0/` with the standard contract
- Mermaid string output that renders correctly in a Mermaid previewer
- Eval on 5 sample files with hand-drawn ground-truth graphs

### Prompt to paste into Claude Code

```
Build services/viz/v0/ — V0 VIZ agent (single-file call graph).

services/viz/v0/pyproject.toml — name "viz-v0", deps: (none beyond stdlib — ast module is built in)

services/viz/v0/src/viz/agent.py:
  def build_call_graph(file_path: str) -> dict:
    Parse file with `ast.parse`. Walk all FunctionDef and ClassDef nodes.
    For each function, find ast.Call inside its body, resolve callee name (best-effort: ast.Attribute -> "obj.method", ast.Name -> name).
    Build edges: caller -> callee. Skip stdlib/builtin calls (configurable list).
    Return {
      "nodes": [{"id":qualified_name,"kind":"function|method|class"}],
      "edges": [{"from":caller_id,"to":callee_id}],
      "mermaid": "graph TD\n    ..."  # generated from nodes+edges
    }

services/viz/v0/src/viz/api.py — CONTRACT:
  get_metadata() returns:
    {"service":"viz","version":"v0",
     "upgrade_from_previous":"Baseline. Single Python file -> Mermaid call graph via AST. NO LLM — pure static analysis. Establishes a free baseline for future LLM versions to beat.",
     "new_capabilities":["AST-based call graph","Mermaid output"],
     "input_schema":{"file_path":"str"},
     "output_schema":{"nodes":"list","edges":"list","mermaid":"str","latency_ms":"float"}}
  run(input) — input requires file_path.

services/viz/v0/main.py — CLI --file <path>, prints mermaid string.

shared/eval-datasets/viz-v0.jsonl — 5 items. Each has file_path (relative to test fixtures dir) and expected_edges (list of [from,to] pairs that MUST be present; extra is OK). CC: create 5 sample .py files with varying complexity (3 funcs, 10 funcs, 1 class+methods, recursive, mutual recursion) in services/viz/v0/fixtures/.

services/viz/v0/eval.py:
  For each item: call run, compute edge recall (expected ∩ produced / expected), edge precision approximation.
  Aggregate. Save to results/viz/v0/run-{timestamp}.json.
  Print summary.

Run eval, show output.

Constraints: V0 is intentionally LLM-free. Cost should be near zero. Latency is the only "performance" axis.
```

### After CC completes
1. Edge recall — does AST catch dynamic dispatch / decorators / lambdas? It won't. Note these failure modes — V1+ may or may not improve them.
2. Render one mermaid output — is it readable, or a hairball?
3. Cost: should be $0. Latency should be sub-second.

---

**Next:** [viz-v1.md](./viz-v1.md)
