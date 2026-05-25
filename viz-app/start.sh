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

# v* 폴더의 키 자동 복사
for v in v20 v19 v15 v10 v4 v3 v2; do
  if [ -f "../${v}/.local_key.txt" ] && [ ! -f ".local_key.txt" ]; then
    cp "../${v}/.local_key.txt" ".local_key.txt"
    echo "[info] ${v} 의 키를 viz-app 으로 복사"
    break
  fi
done

if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ ! -f ".local_key.txt" ]; then
  echo ""
  echo "[warn] 키 없음 → LLM 기능 비활성 (브라우저 ⚙️ 키 모달에서 입력)"
fi

if [ -n "${WEBHOOK_URL:-}" ]; then
  echo "[info] WEBHOOK_URL 설정됨 → Stop 시 알림 보냄"
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
echo "  🚀 VIZ App — Integrated Live HUD"
echo "  http://localhost:8765"
echo ""
echo "  v0~v30 모든 기능 통합:"
echo "  • Live 카드 timeline + 세션 박스 그래프"
echo "  • LLM 활동 요약 (11가지 viz_kind 자동 선택)"
echo "  • SVG 애니메이션 + KPI/Arch/Journey/WhatIf 등"
echo "  • 자연어 시각 요청 / 시간 슬라이더"
echo "  • 코드 품질 + 보안 자동 LLM 체크"
echo "  • 비용 트래커 / 12h 자동 회고"
echo "  • MD 파일 watcher + 우측 사이드바"
echo "  • 배경 파티클 애니메이션 / 다크/라이트"
echo "  • 캡처 / 녹화 / 우클릭→클립보드 / 👍👎 / ⭐"
echo "  Ctrl+C 로 종료"
echo "================================================="
echo ""

exec .venv/bin/python server.py
