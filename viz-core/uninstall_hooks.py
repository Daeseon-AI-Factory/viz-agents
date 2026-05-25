"""V0/V1/V2 공용 hooks 제거."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HOOK_TAG = "VIZ_V0_HUD"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def main() -> int:
    if not SETTINGS_PATH.exists():
        print("settings.json 없음.")
        return 0

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = SETTINGS_PATH.with_name(f"settings.json.bak.{ts}")
    shutil.copy(SETTINGS_PATH, backup)
    print(f"백업: {backup}")
    try:
        settings = json.loads(SETTINGS_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    hooks_map = settings.get("hooks", {})
    removed = 0
    for event in list(hooks_map.keys()):
        new_entries = []
        for entry in hooks_map[event]:
            inner = entry.get("hooks", [])
            kept = [h for h in inner if HOOK_TAG not in h.get("command", "")]
            removed += len(inner) - len(kept)
            if kept:
                entry["hooks"] = kept
                new_entries.append(entry)
        if new_entries:
            hooks_map[event] = new_entries
        else:
            del hooks_map[event]
    if not hooks_map:
        settings.pop("hooks", None)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))
    print(f"{removed}개 hook 제거")
    return 0


if __name__ == "__main__":
    sys.exit(main())
