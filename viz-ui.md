# VIZ Service — Web UI

**[← Index](./viz-README.md)** · **[← v6](./viz-v6.md)**

---

## UI — VIZ dashboard (Mermaid renderer)

### Prompt to paste into Claude Code (after V0 exists)

```
Build services/viz/ui/ — Streamlit dashboard for VIZ with inline Mermaid rendering.

services/viz/ui/pyproject.toml — name "viz-ui", deps: streamlit, streamlit-mermaid (or use components.html with mermaid.js CDN if streamlit-mermaid unavailable)

services/viz/ui/app.py:

import streamlit as st, importlib.util, json
from pathlib import Path

st.set_page_config(page_title="VIZ Service", layout="wide")
st.title("VIZ Service")

# Auto-discover versions same pattern as si/ui.

# Sidebar:
#   - version multi-select
#   - target selector: "single file path" or "package directory path" or "repo root" (v5+) or "platform itself" (v6 only)

# Tabs:
# Tab 1 — Diagrams:
#   For each selected version, render its Mermaid output(s) inline.
#   v0/v1: call graph + import graph
#   v2: + deps mermaid
#   v3: + workflow sequence diagrams (one per entry point)
#   v4: compact / detailed / narrative tabs
#   v5: full profile rendered as a structured panel + diagrams
#   v6: platform overview mermaid
#
# Tab 2 — Profile (v5+):
#   If v5+ ran on a repo, show project_profile.yaml as a structured view:
#     stack section, conventions section, domain section, suggested_agent_config (collapsible code blocks)
#
# Tab 3 — Eval history same pattern as other UIs.

# To render mermaid inline without streamlit-mermaid:
#   components.html("<div class='mermaid'>{mermaid_str}</div><script src='https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js'></script><script>mermaid.initialize({startOnLoad:true});</script>", height=600)

Run streamlit, output URL.
```

---

**[← Back to index](./viz-README.md)**
