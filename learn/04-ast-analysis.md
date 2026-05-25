# 04. Python AST 분석 (코드 → callgraph)

> **viz-core 의 `📦 분석` 기능 원리. LLM 안 씀, 비용 0.**

---

## 한 줄

> Python 코드를 파싱해서 함수/클래스/import/호출 관계를 추출. **LLM 호출 없이 순수 Python `ast` 모듈만** 사용.

---

## AST 란?

```
원본 코드:
   def login(p, h):
       return secrets.compare_digest(p, h)

      ↓ ast.parse()
      
Abstract Syntax Tree (트리 구조):
   Module
     └─ FunctionDef name="login"
          ├─ arguments: [p, h]
          └─ Return
               └─ Call
                    ├─ Attribute "secrets.compare_digest"
                    └─ args: [Name "p", Name "h"]
```

이 트리를 순회 (walk)하면서 클래스/함수/호출 추출.

---

## 추출하는 것들

| 무엇 | 어떻게 |
|---|---|
| 클래스 | `ast.ClassDef` 노드 찾기 |
| 함수 | `ast.FunctionDef`, `ast.AsyncFunctionDef` |
| import | `ast.Import`, `ast.ImportFrom` |
| 함수 호출 | 각 함수 body 안의 `ast.Call` 노드 |

---

## 실제 코드 (단순화)

```python
import ast

def _analyze_python_file(path):
    src = Path(path).read_text()
    tree = ast.parse(src)
    
    classes, functions, imports, calls = [], [], [], []
    
    # 1. 트리 전체 순회 → 클래스/import 추출
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, ...})
        elif isinstance(node, ast.Import):
            imports.append(...)
    
    # 2. top-level 함수 추출
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.append({"name": node.name, ...})
    
    # 3. 각 함수 안 ast.Call 노드 찾아서 호출 관계
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            caller = node.name
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    callee = None
                    if isinstance(sub.func, ast.Name):
                        callee = sub.func.id     # foo() 
                    elif isinstance(sub.func, ast.Attribute):
                        callee = sub.func.attr    # obj.foo()
                    if callee:
                        calls.append({"from": caller, "to": callee})
    
    return {"classes": classes, "functions": functions, 
            "imports": imports, "calls": calls}
```

---

## 한계 (정직)

### 잡는 것
- ✓ 같은 파일 안 함수끼리 호출
- ✓ 클래스 메소드 호출 (이름만)
- ✓ import 문 (직접)

### 못 잡는 것
- ✗ **다른 파일 함수** (multi-file 분석 필요)
- ✗ **동적 dispatch** (`getattr`, `eval`)
- ✗ **메서드 체이닝 깊이** (a.b.c.d() — 마지막 d만)
- ✗ **데코레이터** 안 함수
- ✗ **lambda** 안 호출
- ✗ **재귀** 표시 (제외함, 자기 자신 호출 무시)

→ 가벼운 분석. 정확도 100% 아님. "대략 이런 모양" 정도.

---

## 더 정확하게 하려면

| 도구 | 장점 | 단점 |
|---|---|---|
| `ast` (지금) | 표준 라이브러리, 빠름 | Python만, 단순 |
| `tree-sitter` | 다언어 (JS/TS/Go/Rust), 더 정확 | 의존성 추가 |
| `pylint`, `flake8` | 호출 그래프 더 정확 | 무거움 |
| LLM 분석 | 의미론적 (의도 파악) | 비용 ↑, 느림 |

지금 viz-core는 가장 가벼운 `ast` 사용.

---

## 시각화로 변환

```
analysis = {classes:[], functions:[27개], calls:[33개]}
   ↓
_analyze_to_viz(analysis):
   - calls 가 있으면 → viz_kind="callgraph"
   - 노드 = calls 안 모든 함수 (unique)
   - edges = calls
   - in_degree, out_degree 계산 (계층 배치용)
   ↓
브라우저: renderVizCallgraph(viz_data)
   - 계층 배치 (in_degree=0 → 왼쪽 시작)
   - SVG 화살표 + 점 흐름
```

---

## 비용

**$0.** AST 분석은 LLM 안 씀.

CPU만 사용. 파일 1개 = 수십 ms.

---

## 검증한 정확도

`viz-core/server.py` 의 `_try_summarize` 함수가 부르는 함수:

| 실제 코드 | AST 추출 |
|---|---|
| `_now_ts()` | ✓ |
| `_compact_events()` | ✓ |
| `_call_llm_summary()` | ✓ |
| `_now_iso()` | ✓ |
| `_get_key()` | ✓ |
| `_broadcast()` | ✓ |

**6/6 정확.** 단일 파일 같은 함수끼리 호출은 잘 잡음.

---

## 핵심 이해 체크

- [ ] AST = 코드의 트리 구조
- [ ] `ast.parse()` 로 트리 만들고 `ast.walk()` 로 순회
- [ ] 함수 호출 = `ast.Call` 노드
- [ ] 비용 $0 (LLM 안 씀)
- [ ] 한계: multi-file X, 동적 dispatch X, Python 만

다음: [05-websocket.md](./05-websocket.md)
