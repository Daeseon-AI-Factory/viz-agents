# Service 4: VIZ Team (Code/System/Business/Workflow Analysis + Visualization) — All Versions

**TMUX session:** `tmux new -s viz`
**Versions:** V0 → V6 (7 stages)

---

## What this service does

Analyzes and visualizes code, packages, systems, business logic, and workflows. The "make anyone understand the system" service. Critical because the whole platform's value depends on someone — including the developer six months later — being able to look at the dashboard and grasp what is going on.

Also: V5 is where **repo onboarding / project profile** lives — the analysis pass that runs when a new project is loaded so other services (SI, OPS, ADR) can configure themselves.

---

## Version progression

| File | Upgrade |
|---|---|
| [viz-v0.md](./viz-v0.md) | Single Python file → Mermaid call graph. Baseline. |
| [viz-v1.md](./viz-v1.md) | + multi-file package import graph. |
| [viz-v2.md](./viz-v2.md) | + external dependency analysis (libraries, versions, security flags). |
| [viz-v3.md](./viz-v3.md) | + business workflow extraction (find the main user-facing flow). |
| [viz-v4.md](./viz-v4.md) | + 3-agent split (parser + analyzer + diagrammer). |
| [viz-v5.md](./viz-v5.md) | **+ project profile** (full repo onboarding: stack, conventions, domain). |
| [viz-v6.md](./viz-v6.md) | + cross-service: integrate SI code + QA tests + OPS logs in one unified view. |
| [viz-ui.md](./viz-ui.md) | Streamlit + Mermaid renderer. |

---

## Contract

`services/viz/v<N>/src/viz/api.py` with `get_metadata()` + `run(input)`. Most versions return both structured analysis JSON AND a Mermaid (or other diagram format) string.

---

## Done with VIZ

7 versions built? Write 6 transition ADRs and move on.
