#!/usr/bin/env python3
"""Expose the tail of the HALog2026 USB tether log as command_line JSON."""

from __future__ import annotations

from collections import deque
from datetime import datetime
import json
from pathlib import Path


LOG_PATH = Path("/config/logs/usb_tether/usb_tether.log")
MAX_LINES = 40
MAX_TEXT_CHARS = 8000


def main() -> None:
    if not LOG_PATH.exists():
        print(
            json.dumps(
                {
                    "state": "empty",
                    "line_count": 0,
                    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text": "",
                    "lines": [],
                },
                ensure_ascii=True,
            )
        )
        return

    with LOG_PATH.open("r", encoding="utf-8", errors="replace") as handle:
        lines = [line.rstrip("\n") for line in deque(handle, maxlen=MAX_LINES)]

    text = "\n".join(lines)
    if len(text) > MAX_TEXT_CHARS:
        text = text[-MAX_TEXT_CHARS:]

    stat = LOG_PATH.stat()
    updated = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    state = updated[-8:] if lines else "empty"

    print(
        json.dumps(
            {
                "state": state,
                "line_count": len(lines),
                "updated": updated,
                "text": text,
                "lines": lines,
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
