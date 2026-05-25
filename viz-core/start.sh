#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if lsof -i :8765 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[info] 8765 포트 사용 중 — 기존 서버 종료…"
  kill $(lsof -ti :8765 -sTCP:LISTEN 2>/dev/null) 2>/dev/null || true
  sleep 1
fi

if [ ! -d ".venv" ]; then
  echo "[setup] .venv 생성 중…"
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q "fastapi" "uvicorn[standard]" "httpx"
fi

.venv/bin/python install_hooks.py

# 이전 폴더의 키 자동 복사
for v in viz-app v30 v20 v15 v10 v4; do
  if [ -f "../${v}/.local_key.txt" ] && [ ! -f ".local_key.txt" ]; then
    cp "../${v}/.local_key.txt" ".local_key.txt"
    echo "[info] ${v} 의 키를 viz-core 로 복사"
    break
  fi
done

(
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    sleep 0.4
    curl -s --max-time 0.5 http://127.0.0.1:8765/healthz >/dev/null 2>&1 && {
      open "http://127.0.0.1:8765"
      exit 0
    }
  done
) &

echo ""
echo "================================================="
echo "  🎯 viz-core — AI 출력 시각화 R&D 레이어"
echo "  http://localhost:8765"
echo ""
echo "  단순화 빌드:"
echo "  • 헤더 버튼 1개 (⚙️ 키만)"
echo "  • NOW + 자연어 입력 + 세션 타임라인"
echo "  • 11종 viz_kind 자동 매핑"
echo "  • 우클릭 → 클립보드"
echo "  • ⭐ 즐겨찾기"
echo "  핵심 정의: CORE.md 참고"
echo "  Ctrl+C 로 종료"
echo "================================================="
echo ""

exec .venv/bin/python server.py
