# VIZ Live HUD — V5: Code Deep Visualization

**[← v4](./viz-v4.md)** · **[Roadmap](./viz-roadmap.md)** · **[v6 →](./viz-v6.md)**

---

## V5 — 코드 깊이 시각 (Code Deep Viz)

### Upgrade from V4
V4 = LLM이 그때그때 시각을 만듦 (메커니즘).
V5 = 그 위에 **코드의 의미론적 변화**를 시각화. 단순 diff 넘어 AST/구조 차원.

### Why (본인 비전 매핑)
> "코드를 시각화" — V0~V4는 코드 **활동** 시각 (어떤 도구 썼나). V5는 코드 **변화** 시각.

### Exit criteria
- 함수 추가/제거/이동 시 시각적으로 강조
- import 추가/제거 → 의존성 변화 화살표
- 시그니처 변경 → before/after 함수 박스 비교
- 클래스 상속 구조 변경 → 트리 변화

### 구체 시각화 예시

| 코드 변화 | V5 시각 |
|---|---|
| `def login(user)` → `def login(user, mfa=False)` | 함수 박스 + 새 파라미터 강조 |
| `import bcrypt` 추가 | 의존성 그래프에 새 노드 펄스 |
| `class User` → `class User(Base)` | 상속 트리 변화 |
| 100줄 함수 → 3개 작은 함수로 분할 | "리팩터링" 라벨 + 분할 시각 |
| TODO 주석 추가 | TODO 카운터 +1 + 위치 점멸 |

### Architecture
- 서버: PostToolUse(Edit/Write) 받으면 old/new AST 파싱
- 진단: 함수/클래스/import 단위 변화 추출
- LLM 도움: 의미 있는 변화인지, 어떤 시각이 어울리는지 판단
- 브라우저: 코드 박스 + 변화 강조 (color, animation)

### LLM 프롬프트 (개념)
```
입력: old_code, new_code, file_path
출력: {
  "change_type": "add_function|remove_function|change_signature|add_import|refactor|...",
  "impact": "low|medium|high",
  "summary": "한 줄 요약",
  "highlight_lines": [12, 13, 14],
  "viz_kind": "function_box|dep_graph|inheritance_tree|..."
}
```

### Dependencies
- `ast` (Python) for Python files
- `tree-sitter` (선택, 다언어 지원) 
- 또는 LLM에 raw diff 주고 추출 시키기 (가장 단순)

### Risk
- 큰 파일은 AST 파싱 비용 증가
- 다언어 지원이 어려움 (Python/JS/Go 우선)
- LLM 호출 추가 → 비용 +
- "의미 있는 변화" 판단이 주관적

### V4 와의 차이
- V4 = "viz_kind: diff" 까지만
- V5 = diff 안에 **의미 라벨** (보안 수정, 리팩터링, 새 기능 등) + 시각 강조

---

**다음:** [viz-v6.md](./viz-v6.md)
