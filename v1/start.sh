#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# V0 서버가 같은 포트(8765)에서 돌고 있으면 충돌. 정리 시도.
if lsof -i :8765 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[info] 8765 포트 이미 사용 중. V0 서버 자동 종료 시도…"
  PIDS=$(lsof -ti :8765 -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    kill $PIDS 2>/dev/null || true
    sleep 1
  fi
fi

if [ ! -d ".venv" ]; then
  echo "[setup] .venv 생성 중…"
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q "fastapi" "uvicorn[standard]"
fi

.venv/bin/python install_hooks.py

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
echo "  VIZ V1 Live HUD"
echo "  http://localhost:8765"
echo "  변경점: 선택지 카드 렌더링 + 세션 색 구분"
echo "  Ctrl+C 로 종료"
echo "================================================="
echo ""

exec .venv/bin/python server.py
