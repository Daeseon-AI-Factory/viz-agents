# AI 가이드 — viz-core 와 함께 일할 때

이 파일을 **본인 AI 도구의 system prompt / Custom Instructions** 에 박으면, AI 가 응답할 때마다 viz-core 가 자동 인식하는 형식으로 시각 명세를 넣어줍니다.

---

## 복붙 프롬프트 (짧은 버전)

```
You are paired with viz-core (https://github.com/viz-core), an AI-output
visualization layer. When your answer would benefit from a diagram, append
a viz-spec code fence at the end. The user's main answer is unchanged;
viz-core picks the fence up and renders it in a side window.

Format:
  ```viz-spec
  {"viz_kind": "<one of 23 kinds>", "data": {...}}
  ```

Choose viz_kind based on intent:
- userflow: user journey with branches (decision nodes)
- screenmap: screens + transitions (UX wireframes)
- depgraph: service dependencies (microservices)
- crud: entity × role permissions matrix
- callgraph: function call graph in code
- arch: system architecture layers
- timeseries: trends over time (use Chart.js shape)
- bar: category comparison
- funnel: conversion stages
- heatmap: 2D distribution (time × metric)
- kanban: TODO/DOING/DONE board
- waterfall: distributed trace spans
- cohort: retention matrix
- kpi: business metrics cards
- gauge: single number with max
- diff: before/after code
- table: rows × columns
- flow: linear steps with status
- badge: single status label
- code: code snippet
- animation: data flowing between nodes
- journey: simple user journey (no branches)
- whatif: current vs. after comparison
- mermaid: anything not in the above (Mermaid syntax inside `code`)

Rules:
- The viz-spec block is sidecar. Never reference it in the main answer.
- One block per answer is enough. Multiple OK if truly separate views.
- If unsure, omit. Better no viz than wrong viz.
- Keep data terse. Real numbers, not placeholders.
```

---

## 짧은 한국어 버전 (Claude Code / 한국어 AI 용)

```
viz-core 와 페어로 일합니다. 답변이 그림으로 더 명료해질 때, 답변 끝에
viz-spec 코드펜스를 추가하세요. 메인 답변은 그대로, viz-core 가 마커만
뽑아 옆 창에 그립니다.

형식:
  ```viz-spec
  {"viz_kind": "...", "data": {...}}
  ```

선택 가능한 viz_kind (23종):
userflow, screenmap, depgraph, crud, callgraph, arch, timeseries, bar,
funnel, heatmap, kanban, waterfall, cohort, kpi, gauge, diff, table,
flow, badge, code, animation, journey, whatif, mermaid

규칙:
- viz-spec 블록은 사이드카. 메인 답변에서 절대 언급 X.
- 한 답변에 1개면 충분. 별도 시각이면 여러 개 OK.
- 애매하면 빼는 게 나음. 잘못된 viz 보다 viz 없는 게 나음.
- 실제 데이터 / 짧게.
```

---

## 어디에 박나?

| AI 도구 | 박는 위치 |
|---|---|
| **Claude Code** | `~/.claude/CLAUDE.md` 또는 프로젝트 `CLAUDE.md` 에 추가 |
| **ChatGPT** | Settings → Personalization → Custom Instructions |
| **Cursor** | `.cursor/rules` 또는 프로젝트 rule 파일 |
| **Claude 웹** | 프로젝트 설정 → System Prompt |
| **Continue.dev** | `~/.continue/config.json` `systemMessage` |
| **자체 agent** | 자체 system prompt 에 박기 |

---

## 보내는 방법 (자동화)

AI 응답을 받는 측에서 viz-core 로 POST:

```bash
curl -X POST http://localhost:8765/viz/spec \
  -H 'Content-Type: application/json' \
  -d '{"text": "<AI 응답 전문>", "source": "claude-code"}'
```

- viz-core 가 텍스트 안의 모든 `viz-spec` 마커 자동 추출
- WebSocket 으로 브라우저 옆 탭에 즉시 푸시
- **LLM 호출 0** — 빠르고 비용 없음

Claude Code 의 경우 `~/.claude/settings.json` 의 hooks 에서 자동:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "jq -Rs '{text:.}' < /dev/stdin | curl -s -X POST http://localhost:8765/viz/spec -d @-"
      }]
    }]
  }
}
```

---

## 23종 viz_kind — 최소 schema

(각 kind 의 자세한 예시는 `/spec` 페이지 또는 `/showcase` 참고)

| viz_kind | data 필수 키 |
|---|---|
| diff | `file, before, after, lang` |
| gauge | `label, value, max, unit` |
| table | `headers, rows` |
| flow | `steps:[{name,status}]` |
| badge | `label, tone` |
| code | `lang, code` |
| animation | `nodes:[{id,label}], flow:[...], duration_ms` |
| kpi | `kpis:[{label,value,trend,delta}]` |
| journey | `persona, stages:[{name,icon,drop}]` |
| arch | `layers:[{name,components}], active_layer` |
| whatif | `title, current, after, recommendation` |
| mermaid | `code, title` |
| callgraph | `nodes, edges, entries` |
| timeseries | `title, labels, series:[{label,values,color}]` |
| bar | `title, labels, values` (또는 `series`) |
| funnel | `title, stages:[{name,value}]` |
| heatmap | `title, labels_x, labels_y, matrix` |
| kanban | `title, columns:[{name,cards:[...]}]` |
| waterfall | `title, spans:[{name,service,start_ms,duration_ms}]` |
| cohort | `title, cohorts:[{label,initial,retention:[...]}]` |
| crud | `title, entities, actors, matrix` |
| userflow | `title, nodes:[{id,label,kind}], edges:[{from,to,label}]` |
| screenmap | `title, screens:[{id,title,x,y,items}], transitions:[{from,to,action}]` |
| depgraph | `title, services:[{id,label,kind}], deps:[{from,to,kind}]` |
