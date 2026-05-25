#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# 8765 포트 이미 사용 중이면 기존 서버 종료
if lsof -i :8765 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[info] 8765 포트 사용 중 — 기존 서버 자동 종료…"
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

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo ""
  echo "[warn] ANTHROPIC_API_KEY 없음 → LLM 요약 비활성 (규칙 기반 fallback 사용)"
  echo "  활성화하려면 새 터미널에서:"
  echo "  export ANTHROPIC_API_KEY='sk-ant-...'"
  echo "  ./start.sh"
else
  echo "[info] LLM 요약 활성 (모델: claude-haiku-4-5)"
fi

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
echo "  VIZ V2 Live HUD"
echo "  http://localhost:8765"
echo "  변경점: NOW 한 줄 + Stop마다 LLM 활동 요약"
echo "  Ctrl+C 로 종료"
echo "================================================="
echo ""

exec .venv/bin/python server.py
