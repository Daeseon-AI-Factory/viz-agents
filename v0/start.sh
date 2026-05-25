#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Setup virtualenv if not present.
if [ ! -d ".venv" ]; then
  echo "[setup] .venv 생성 중…"
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q "fastapi" "uvicorn[standard]"
  echo "[setup] 완료"
fi

# Install hooks (idempotent — safe to run repeatedly).
.venv/bin/python install_hooks.py

# Open browser tab once server is up.
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
echo "  VIZ V0 Live HUD"
echo "  http://localhost:8765"
echo "  Ctrl+C 로 종료"
echo "================================================="
echo ""

exec .venv/bin/python server.py
