# VIZ Service — V3

**[← Index](./viz-README.md)** · **[← v2](./viz-v2.md)** · **[v4 →](./viz-v3.md)**

---

## V3 — Business workflow extraction

### Upgrade from V2
V0–V2 produce structural views (which code calls which, which file imports which, which deps exist). V3 finds the **business workflow**: starting from entry points (CLI `main`, FastAPI/Flask routes, scheduled jobs), trace the highest-value paths through the code and present them as a sequence diagram or flowchart, abstracted up from individual function calls.

This is where the platform becomes useful for "what does this system actually do?" — not "what code is here?"

### Exit criteria
- Identifies entry points (CLI mains, web routes, scheduled jobs)
- For each entry point, traces through the call graph (V0/V1's output) and produces an LLM-summarized workflow
- Outputs a Mermaid sequenceDiagram or flowchart per workflow
- Eval: hand-labeled "main workflow" per fixture package — does V3's top extracted workflow match?

### Prompt to paste into Claude Code

```
Build services/viz/v3/ — adds business workflow extraction.

STEP 1: Read services/viz/v2/.

STEP 2: Build services/viz/v3/.

services/viz/v3/src/viz/workflows.py:
  def find_entry_points(pkg_analysis) -> list[dict]:
    Heuristic detection:
      - `if __name__ == "__main__":` blocks
      - Functions decorated with @app.route, @router.get/post, @app.task (celery), @cli.command
      - Functions named main, run, handler, lambda_handler
    Return [{"file":path,"function":name,"kind":"cli|web|task|main"}].

  def trace_workflow_llm(entry: dict, call_graph: dict, max_depth=6) -> dict:
    Walk the call graph from entry. Collect the call chain up to max_depth.
    LLM: "Given this call chain, summarize the business workflow in 5-10 steps. Output JSON: {\"name\":str,\"steps\":[{\"step\":int,\"description\":str,\"function\":str}],\"sequence_mermaid\":str (Mermaid sequenceDiagram)}. ONLY JSON."
    Return parsed dict.

services/viz/v3/src/viz/agent.py:
  In api.run:
    Get V2 output.
    entries = find_entry_points(...)
    workflows = [trace_workflow_llm(e, call_graph) for e in entries]
    Return everything + {"workflows": workflows}

services/viz/v3/src/viz/api.py:
  "upgrade_from_previous":"V2 produced structural views (calls, imports, deps) but no narrative of what the system DOES. V3 finds entry points (CLI mains, web routes, scheduled tasks), traces call chains from each, and uses an LLM to summarize each into a 5-10 step business workflow with a Mermaid sequence diagram. This is the 'what does this thing do' view.",
  "new_capabilities":["entry point detection","call-chain tracing from entry","LLM workflow summarization","sequence diagram output"]

shared/eval-datasets/viz-v3.jsonl — 3 fixture packages, each with:
  - a clear main entry (e.g. a small CLI todo app, a tiny FastAPI service, a scheduled report-generator)
  - expected_workflow_name (string the LLM output should approximate)
  - expected_steps_min/max (count range)

services/viz/v3/eval.py:
  workflow_name_match_rate (LLM-as-judge), steps_count_in_range_rate, entry_points_recall.
```

### After CC completes
1. Open one workflow Mermaid in a previewer. Does it read like a human-written sequence diagram or like noise?
2. Are entry points discovered correctly? Did V3 miss any (e.g. cron-only)?
3. Cost per workflow — one LLM call per entry point. At 10 entry points, what's the bill?

---

**Next:** [viz-v4.md](./viz-v4.md)
