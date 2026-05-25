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

# V2에서 저장한 키가 있으면 V3도 사용 가능 (각 버전 폴더의 .local_key.txt)
# 처음 V3 실행이면 우상단 ⚙️ 키 설정 모달에서 한 번만 입력
if [ -f "../v2/.local_key.txt" ] && [ ! -f ".local_key.txt" ]; then
  cp "../v2/.local_key.txt" ".local_key.txt"
  echo "[info] V2의 키를 V3로 자동 복사함"
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
echo "  VIZ V3 Live HUD"
echo "  http://localhost:8765"
echo "  변경점: 카드 timeline → 세션별 흐름 그래프"
echo "  Ctrl+C 로 종료"
echo "================================================="
echo ""

exec .venv/bin/python server.py
