#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

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

# 이전 버전의 키 자동 복사 (있으면)
for prev in v3 v2; do
  if [ -f "../${prev}/.local_key.txt" ] && [ ! -f ".local_key.txt" ]; then
    cp "../${prev}/.local_key.txt" ".local_key.txt"
    echo "[info] ${prev} 의 키를 V20로 자동 복사함"
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
echo "  VIZ V20 Live HUD"
echo "  http://localhost:8765"
echo "  변경점: 작업 디스크립션마다 다른 시각 자동 생성"
echo "         (diff / gauge / table / flow / badge)"
echo "  Ctrl+C 로 종료"
echo "================================================="
echo ""

exec .venv/bin/python server.py
