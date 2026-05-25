"""Install VIZ V1 hooks into ~/.claude/settings.json.

V0와 동일한 endpoint(http://localhost:8765/event) 사용.
V0 hooks가 이미 박혀있으면 V1으로 자동 업그레이드 (태그 같음).
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HOOK_TAG = "VIZ_V0_HUD"  # v0 와 같은 태그 — 같은 endpoint 공유
ENDPOINT = "http://localhost:8765/event"

HOOK_COMMAND = (
    f"cat | curl -s --max-time 1 -X POST "
    f"-H 'Content-Type: application/json' "
    f"--data-binary @- {ENDPOINT} >/dev/null 2>&1 || true "
    f"# {HOOK_TAG}"
)

EVENTS = [
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "SubagentStop",
    "Notification",
    "SessionStart",
]

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def already_installed(hook_entries: list[dict]) -> bool:
    for entry in hook_entries:
        for hook in entry.get("hooks", []):
            if HOOK_TAG in hook.get("command", ""):
                return True
    return False


def main() -> int:
    if SETTINGS_PATH.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = SETTINGS_PATH.with_name(f"settings.json.bak.{ts}")
        shutil.copy(SETTINGS_PATH, backup)
        print(f"백업: {backup}")
        try:
            settings = json.loads(SETTINGS_PATH.read_text())
        except json.JSONDecodeError as e:
            print(f"오류: settings.json 파싱 실패 — {e}", file=sys.stderr)
            return 1
    else:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        settings = {}
        print(f"새 파일 생성: {SETTINGS_PATH}")

    hooks_map = settings.setdefault("hooks", {})

    installed = 0
    skipped = 0
    for event in EVENTS:
        entries = hooks_map.setdefault(event, [])
        if already_installed(entries):
            print(f"  {event}: 이미 설치됨")
            skipped += 1
            continue
        entries.append({
            "matcher": ".*" if event in ("PreToolUse", "PostToolUse") else "",
            "hooks": [{"type": "command", "command": HOOK_COMMAND}],
        })
        installed += 1
        print(f"  {event}: 설치")

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))
    print(f"\n신규 {installed}개 / 스킵 {skipped}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
